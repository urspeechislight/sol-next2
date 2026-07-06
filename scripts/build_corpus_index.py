#!/usr/bin/env python3
"""Build the corpus full-text index (``data/corpus.db``).

Thin driver: projections and SQL live in ``backend.build.corpus``; the
build loop and CLI shell live in ``backend.build.runner``. Run on
buildhost::

    uv run python scripts/build_corpus_index.py
    uv run python scripts/build_corpus_index.py --book-table-only
"""

from __future__ import annotations

import argparse
import sqlite3
from typing import Any

from backend.build import corpus as corpus_build
from backend.build import runner
from backend.core.constants import ARTIFACT__CORPUS_DB
from backend.core.paths import data_path
from backend.models.book import Book


def _project(book: Book) -> dict[str, list[dict[str, Any]]] | None:
    """Project one book into FTS page rows, or None when it has no pages."""
    rows = corpus_build.index_rows(book.urn)
    return {"pages": rows} if rows else None


def _finish(con: sqlite3.Connection, books: list[Book]) -> dict[str, int]:
    """Build the filter table from the whole catalog after the page loop."""
    rows = corpus_build.book_table_rows(books)
    corpus_build.build_book_table(con, rows)
    return {"book_table": len(rows)}


def _build(args: argparse.Namespace) -> dict[str, object]:
    """Full FTS build, or only the filter-table refresh on an existing index."""
    if args.book_table_only:
        return {"book_table": corpus_build.refresh_book_table(args.out)}
    return runner.build_catalog_artifact(
        args.out,
        corpus_build.CORPUS_SCHEMA,
        corpus_build.TABLES,
        _project,
        limit=args.limit,
        finish=_finish,
    )


def _add_args(parser: argparse.ArgumentParser) -> None:
    """Register the corpus-specific flag."""
    parser.add_argument(
        "--book-table-only",
        action="store_true",
        help="rebuild only the book filter table on an existing index",
    )


def main() -> None:
    """Run the corpus index build CLI."""
    runner.run_build_cli(
        "Build the corpus FTS index + book filter table.",
        data_path(ARTIFACT__CORPUS_DB),
        _build,
        add_args=_add_args,
    )


if __name__ == "__main__":
    main()
