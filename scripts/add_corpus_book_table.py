#!/usr/bin/env python3
"""One-off: (re)build the ``book(urn, category, title, volume)`` filter table on
an existing ``data/corpus.db`` without rebuilding the FTS index. Idempotent
(drops + recreates the table). Run on buildhost, then restart the backend so it
re-opens the index::

    uv run python scripts/add_corpus_book_table.py
"""

from __future__ import annotations

import sqlite3

from backend.build import corpus as corpus_build
from backend.core.paths import data_path
from backend.repositories import books as books_repo

_DB = data_path("corpus.db")


def main() -> None:
    """Populate the book filter table from the catalog index."""
    if not _DB.exists():
        raise SystemExit(f"Corpus index missing: {_DB}")
    books, _ = books_repo.list_books()
    rows = corpus_build.book_table_rows(books)
    con = sqlite3.connect(_DB)
    try:
        corpus_build.build_book_table(con, rows)
        con.commit()
    finally:
        con.close()
    print(f"book table ready: {len(rows)} books")


if __name__ == "__main__":
    main()
