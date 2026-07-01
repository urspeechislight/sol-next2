"""Build layer: materialize the read-only corpus full-text index artifact.

Schema, INSERT statements, and row projections for ``data/corpus.db`` (the
FTS5 index + the ``book(urn, category, title, volume)`` filter table). Each
page is stored twice: a ``fold`` column (``patterns.fold_search`` output)
that FTS5 indexes for matching, and the original ``content`` (UNINDEXED)
for fold-aware snippet display. This is the WRITE side; the served search
queries live in ``backend.repositories.corpus``. The connection lifecycle
and build loop live in ``backend.build.runner``. CENTRAL-005 permits the
DDL/INSERT SQL here.

``BOOK_SCHEMA`` keeps its ``DROP TABLE`` because the filter table is also
rebuilt in place on an existing index (``build_corpus_index.py
--book-table-only``) without redoing the multi-hour FTS build.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from pathlib import Path

from backend.models.book import Book
from backend.patterns import fold_search
from backend.repositories import books as books_repo
from backend.repositories import reader as reader_repo

CORPUS_SCHEMA: str = """
CREATE VIRTUAL TABLE pages USING fts5(
  fold,
  content UNINDEXED,
  urn UNINDEXED,
  page UNINDEXED,
  tokenize = 'unicode61 remove_diacritics 2'
);
"""

BOOK_SCHEMA: str = """
DROP TABLE IF EXISTS book;
CREATE TABLE book (
  urn      TEXT PRIMARY KEY,
  category TEXT NOT NULL DEFAULT '',
  title    TEXT NOT NULL DEFAULT '',
  volume   INTEGER
);
CREATE INDEX idx_book_category ON book (category);
CREATE INDEX idx_book_title ON book (title);
"""

_PAGE_INSERT = "INSERT INTO pages (fold, content, urn, page) VALUES (:fold, :content, :urn, :page)"
_BOOK_INSERT = (
    "INSERT INTO book (urn, category, title, volume) VALUES (:urn, :category, :title, :volume)"
)

TABLES: dict[str, str] = {"pages": _PAGE_INSERT}


def index_rows(urn: str) -> list[dict[str, Any]]:
    """Project one book's page rows into corpus index rows (folded + original).

    A corrupt page row raises ``ReaderSourceError`` here; the build must
    crash loudly rather than write a silently-incomplete index.
    """
    return [
        {"fold": fold_search(r.content), "content": r.content, "urn": urn, "page": r.page}
        for r in reader_repo.page_rows(urn)
    ]


def book_table_rows(books: list[Book]) -> list[dict[str, Any]]:
    """Project catalog books into ``book`` filter-table rows.

    The single source of the URN to (category, title, volume) projection,
    shared by the full index build and the ``--book-table-only`` refresh.
    """
    return [
        {"urn": b.urn, "category": b.category, "title": b.title_ar, "volume": b.volume}
        for b in books
    ]


def build_book_table(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """(Re)create + populate the URN to (category, title, volume) filter table."""
    con.executescript(BOOK_SCHEMA)
    con.executemany(_BOOK_INSERT, rows)


def refresh_book_table(out: Path) -> int:
    """Rebuild only the filter table on an existing index; return the row count.

    The legitimate residual of the one-off ``add_corpus_book_table`` script:
    refreshing the filter table after a catalog re-ingest without redoing
    the multi-hour FTS build. Fails loud when the index is absent.
    """
    if not out.exists():
        raise SystemExit(f"Corpus index missing: {out}")
    books, _ = books_repo.list_books()
    rows = book_table_rows(books)
    con = sqlite3.connect(out)
    try:
        build_book_table(con, rows)
        con.commit()
    finally:
        con.close()
    return len(rows)
