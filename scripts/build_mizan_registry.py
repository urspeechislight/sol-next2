#!/usr/bin/env python3
"""Build the Mizan al-I'tidal name registry artifact (ADR-0001).

Reads the four Mizan volumes out of the corpus full-text index
(``data/corpus.db``), segments each numbered narrator biography, and projects
the opening name of every entry into its onomastic components. Emits a compact
read-only SQLite store plus a decoded JSON export under ``data/``.

Thin driver: the schema, segmentation, and name decomposition live in
``backend.build.mizan`` + ``backend.build.mizan_names``; the artifact lifecycle
and CLI shell live in ``backend.build.runner``. Run on titan::

    uv run python scripts/build_mizan_registry.py
    uv run python scripts/build_mizan_registry.py --out data/mizan_registry.db
"""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.build import mizan, runner
from backend.core.constants import ARTIFACT__CORPUS_DB, ARTIFACT__MIZAN_DB, ARTIFACT__MIZAN_JSON
from backend.core.paths import data_path


def _build(args: argparse.Namespace) -> dict[str, object]:
    """Materialize the Mizan registry DB + JSON from the corpus index."""
    report = mizan.build(args.source, args.out, args.json)
    return dict(report)


def _add_args(parser: argparse.ArgumentParser) -> None:
    """Register the Mizan-specific source + JSON-export paths."""
    parser.add_argument("--source", type=Path, default=data_path(ARTIFACT__CORPUS_DB))
    parser.add_argument("--json", type=Path, default=data_path(ARTIFACT__MIZAN_JSON))


def main() -> None:
    """Run the Mizan registry build CLI."""
    runner.run_build_cli(
        "Build the Mizan al-I'tidal name registry SQLite artifact.",
        data_path(ARTIFACT__MIZAN_DB),
        _build,
        supports_limit=False,
        add_args=_add_args,
    )


if __name__ == "__main__":
    main()
