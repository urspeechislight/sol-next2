#!/usr/bin/env python3
"""Build the read-only narrator registry SQLite artifact (ADR-0001).

Extracts the authoritative narrator store from sol-next3's Postgres (read-only;
never writes into the sol-next3 tree) and projects it one-to-one into a compact
SQLite database under sol-next2's ``data/``. The backend opens this artifact
read-only and serves ``/api/narrators`` from it with near-zero resident memory.

Extraction goes through ``psql`` one table at a time (one JSON object per
output line, ON_ERROR_STOP so a mid-stream failure aborts); the schema, INSERT
statements, and per-table extraction SQL live in ``backend.build.rijal``; the
artifact lifecycle and CLI shell live in ``backend.build.runner``. The DSN
comes from ``--pg-dsn`` or ``SOL_RIJAL_PG_DSN`` (read through
``backend.core.settings``); there is no default — a missing DSN aborts loudly.
Run on buildhost::

    uv run python scripts/build_registry.py --pg-dsn "$SOL_RIJAL_PG_DSN"
"""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any, Final

from backend.build import rijal as rijal_build
from backend.build import runner
from backend.core.constants import ARTIFACT__REGISTRY_DB
from backend.core.paths import data_path
from backend.core.settings import get_settings

_MIN_LIVE_FRACTION: Final[float] = 0.8
_PSQL: Final[tuple[str, ...]] = ("psql",)


def _run_psql(dsn: str, query: str) -> str:
    """Run one query through psql, failing loudly (stderr propagated) on error."""
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell interpolation
        [*_PSQL, dsn, "-At", "-v", "ON_ERROR_STOP=1", "-c", query],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"psql extraction failed ({proc.returncode}):\n{proc.stderr.strip()}")
    return proc.stdout


def _extract_rows(dsn: str, query: str) -> list[dict[str, Any]]:
    """Extract one table as JSON objects, one per psql output line.

    An empty result is a hard failure: every authoritative table is populated,
    so zero rows means the extraction is broken, not that the table is empty.
    """
    lines = [line for line in _run_psql(dsn, query).splitlines() if line.strip()]
    if not lines:
        raise SystemExit(f"psql extraction returned no rows for: {query[:60]}...")
    return [json.loads(line) for line in lines]


def _live_narrator_count(dsn: str) -> int:
    """Read the live Postgres narrator count used by the completeness guard."""
    return int(_run_psql(dsn, rijal_build.LIVE_NARRATOR_COUNT).strip())


def _guard_narrator_count(dsn: str, inserted: int) -> None:
    """Abort unless the artifact carries a plausible share of live narrators."""
    live = _live_narrator_count(dsn)
    if inserted == 0 or inserted < live * _MIN_LIVE_FRACTION:
        raise SystemExit(
            f"narrator count guard failed: inserted {inserted} of {live} live rows "
            f"(floor {live * _MIN_LIVE_FRACTION:.0f}); aborting with a partial artifact"
        )


def _build(args: argparse.Namespace) -> dict[str, object]:
    """Extract every authoritative table and materialize the registry artifact."""
    dsn = args.pg_dsn or get_settings().rijal_pg_dsn
    if not dsn:
        raise SystemExit("no Postgres DSN: pass --pg-dsn or set SOL_RIJAL_PG_DSN")
    con = runner.create_artifact(args.out, rijal_build.NARRATOR_SCHEMA)
    try:
        counts: dict[str, int] = {}
        for table, query in rijal_build.NARRATOR_QUERIES.items():
            rows = _extract_rows(dsn, query)
            with con:
                con.executemany(rijal_build.TABLES[table], rows)
            counts[table] = len(rows)
        _guard_narrator_count(dsn, counts["narrator"])
        runner.finalize(con)
    finally:
        con.close()
    return dict(counts)


def _add_args(parser: argparse.ArgumentParser) -> None:
    """Register the registry-specific source arguments."""
    parser.add_argument(
        "--pg-dsn",
        default=None,
        help="read-only Postgres DSN of sol-next3's narrator store "
        "(defaults to SOL_RIJAL_PG_DSN from the environment)",
    )


def main() -> None:
    """Run the registry build CLI."""
    runner.run_build_cli(
        "Build the narrator registry SQLite artifact from sol-next3's Postgres.",
        data_path(ARTIFACT__REGISTRY_DB),
        _build,
        supports_limit=False,
        add_args=_add_args,
    )


if __name__ == "__main__":
    main()
