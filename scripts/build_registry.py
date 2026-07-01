#!/usr/bin/env python3
"""Build the read-only narrator registry SQLite artifact (ADR-0001).

Reads sol-next's pipeline-produced corpus JSON (read-only; never writes into
the sol-next tree) and projects only the served fields into a compact SQLite
database under sol-next2's ``data/``. The backend opens this artifact
read-only and serves ``/api/rijal`` + ``/api/canonical`` from it with
near-zero resident memory, instead of holding ~900 MB of JSON in RAM.

Thin driver: projections and SQL live in ``backend.build.rijal``; the
artifact lifecycle and CLI shell live in ``backend.build.runner``. Pass 1
covers rijal + canonical; the 3.3 GB history corpus is a later pass. Run on
buildhost::

    uv run python scripts/build_registry.py
    uv run python scripts/build_registry.py --corpus /path/corpus.json --out data/registry.db
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

from backend.build import rijal as rijal_build
from backend.build import runner
from backend.core.paths import data_path

_SOLNEXT_RIJAL: Final[Path] = Path.home() / "code" / "sol-next" / "data" / "rijal"


def _build(args: argparse.Namespace) -> dict[str, object]:
    """Materialize the registry artifact from the two corpus JSON arrays."""
    con = runner.create_artifact(args.out, rijal_build.REGISTRY_SCHEMA)
    try:
        rijal_rows = [
            rijal_build.rijal_row(i, e) for i, e in enumerate(rijal_build.load_array(args.corpus))
        ]
        with con:
            con.executemany(rijal_build.TABLES["rijal"], rijal_rows)
        canon_rows = [
            rijal_build.canonical_row(e)
            for e in rijal_build.load_array(args.canonical)
            if e.get("canonical_id") is not None
        ]
        with con:
            con.executemany(rijal_build.TABLES["canonical"], canon_rows)
        runner.finalize(con)
    finally:
        con.close()
    return {"rijal": len(rijal_rows), "canonical": len(canon_rows)}


def _add_args(parser: argparse.ArgumentParser) -> None:
    """Register the registry-specific source paths."""
    parser.add_argument("--corpus", type=Path, default=_SOLNEXT_RIJAL / "corpus.json")
    parser.add_argument("--canonical", type=Path, default=_SOLNEXT_RIJAL / "canonical.json")


def main() -> None:
    """Run the registry build CLI."""
    runner.run_build_cli(
        "Build the narrator registry SQLite artifact.",
        data_path("registry.db"),
        _build,
        supports_limit=False,
        add_args=_add_args,
    )


if __name__ == "__main__":
    main()
