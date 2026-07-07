#!/usr/bin/env python3
"""Build the read-only narrator registry SQLite artifact (ADR-0001).

Reads sol-next's pipeline-produced corpus (read-only; never writes into the
sol-next tree) and projects the served fields into a compact SQLite database
under sol-next2's ``data/``. The backend opens this artifact read-only and
serves ``/api/rijal`` + ``/api/person`` from it with near-zero resident memory.

Thin driver: per-entry rijal projections live in ``backend.build.rijal``; the
enriched ``person`` corpus (junk-excluded, over-merge-split, death-reconciled,
with reliability, stance, teacher/student edges, and history events) lives in
``backend.build.authority``; the artifact lifecycle and CLI shell live in
``backend.build.runner``. The 3.4 GB history corpus is streamed for the
event/history-actor pass by default; ``--no-history`` builds the rijal
enrichment alone. Run on buildhost::

    uv run python scripts/build_registry.py
    uv run python scripts/build_registry.py --no-history --out data/registry.db
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

from backend.build import authority, runner
from backend.build import rijal as rijal_build
from backend.core.constants import ARTIFACT__REGISTRY_DB
from backend.core.paths import data_path

_SOLNEXT_RIJAL: Final[Path] = Path.home() / "code" / "sol-next" / "data" / "rijal"
_SOLNEXT_HISTORY: Final[Path] = (
    Path.home() / "code" / "sol-next" / "data" / "history_corpus_v5.json"
)


def _build(args: argparse.Namespace) -> dict[str, object]:
    """Materialize the registry artifact: per-entry rijal plus the enriched person corpus."""
    con = runner.create_artifact(args.out, rijal_build.REGISTRY_SCHEMA + authority.PERSON_SCHEMA)
    try:
        rijal_rows = [
            rijal_build.rijal_row(i, e) for i, e in enumerate(rijal_build.load_array(args.corpus))
        ]
        with con:
            con.executemany(rijal_build.TABLES["rijal"], rijal_rows)
        history = None if args.no_history else args.history
        with con:
            person_counts = authority.build_person_tables(
                con, args.canonical, args.corpus_jsonl, history
            )
        runner.finalize(con)
    finally:
        con.close()
    return {"rijal": len(rijal_rows), **person_counts}


def _add_args(parser: argparse.ArgumentParser) -> None:
    """Register the registry-specific source paths."""
    parser.add_argument("--corpus", type=Path, default=_SOLNEXT_RIJAL / "corpus.json")
    parser.add_argument("--canonical", type=Path, default=_SOLNEXT_RIJAL / "canonical.json")
    parser.add_argument("--corpus-jsonl", type=Path, default=_SOLNEXT_RIJAL / "corpus.jsonl")
    parser.add_argument("--history", type=Path, default=_SOLNEXT_HISTORY)
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="build the rijal enrichment without the history event pass",
    )


def main() -> None:
    """Run the registry build CLI."""
    runner.run_build_cli(
        "Build the narrator registry SQLite artifact.",
        data_path(ARTIFACT__REGISTRY_DB),
        _build,
        supports_limit=False,
        add_args=_add_args,
    )


if __name__ == "__main__":
    main()
