"""Build layer: materialize the read-only corpus full-text index artifact.

DDL + INSERT helpers that build ``data/corpus.db`` (the FTS5 index + the
``book(urn, category, title, volume)`` filter table) from projected page rows.
This is the WRITE side; the served search queries live in
``backend.repositories.corpus``. CENTRAL-005 permits the DDL/INSERT SQL here.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from backend.models.book import Book

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

_INSERT = "INSERT INTO pages (fold, content, urn, page) VALUES (:fold, :content, :urn, :page)"
_BOOK_INSERT = (
    "INSERT OR REPLACE INTO book (urn, category, title, volume) "
    "VALUES (:urn, :category, :title, :volume)"
)


def create_index(out: Path) -> sqlite3.Connection:
    """Create a fresh corpus index at ``out`` and apply the FTS schema."""
    if out.exists():
        out.unlink()
    con = sqlite3.connect(out)
    con.executescript(CORPUS_SCHEMA)
    return con


def insert_pages(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """Insert projected page rows (``fold``/``content``/``urn``/``page``)."""
    con.executemany(_INSERT, rows)


def book_table_rows(books: list[Book]) -> list[dict[str, Any]]:
    """Project catalog books into ``book`` filter-table rows — the single source
    of the URN -> (category, title, volume) projection, shared by the index
    builder and the book-table re-migration script."""
    return [
        {"urn": b.urn, "category": b.category, "title": b.title_ar, "volume": b.volume}
        for b in books
    ]


def build_book_table(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """(Re)create + populate the URN -> (category, title, volume) filter table."""
    con.executescript(BOOK_SCHEMA)
    con.executemany(_BOOK_INSERT, rows)
