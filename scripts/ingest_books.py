#!/usr/bin/env python3
"""Build ``data/books_index.json`` from the upstream corpus frontmatter.

Thin driver: the walk, normalizers, and payload assembly live in
``backend.build.catalog``; the CLI shell lives in ``backend.build.runner``.
Run::

    uv run python scripts/ingest_books.py
"""

from __future__ import annotations

import argparse

from backend.build import catalog, runner
from backend.core.constants import ARTIFACT__BOOKS_INDEX
from backend.core.paths import data_path


def _build(args: argparse.Namespace) -> dict[str, object]:
    """Build the catalog index at ``--out``."""
    return catalog.build(args.out)


def main() -> None:
    """Run the catalog ingest CLI."""
    runner.run_build_cli(
        "Build the book catalog index from corpus frontmatter.",
        data_path(ARTIFACT__BOOKS_INDEX),
        _build,
        supports_limit=False,
    )


if __name__ == "__main__":
    main()
