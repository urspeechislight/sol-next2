"""Build layer: materialize the read-only narrator registry artifact.

DDL + INSERT helpers that turn sol-next's projected rijal/canonical rows into
``data/registry.db``. This is the WRITE side; the served queries live in
``backend.repositories.registry``. CENTRAL-005 permits the DDL/INSERT SQL here.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

REGISTRY_SCHEMA: str = """
CREATE TABLE rijal (
  id               INTEGER PRIMARY KEY,
  full_name        TEXT NOT NULL,
  kunya            TEXT NOT NULL DEFAULT '',
  nisba            TEXT NOT NULL DEFAULT '',
  tradition        TEXT NOT NULL DEFAULT '',
  death_year       TEXT NOT NULL DEFAULT '',
  birth_year       TEXT NOT NULL DEFAULT '',
  category         TEXT NOT NULL DEFAULT 'clean',
  teacher_count    INTEGER NOT NULL DEFAULT 0,
  student_count    INTEGER NOT NULL DEFAULT 0,
  reliability_term TEXT NOT NULL DEFAULT '',
  reliability_grade TEXT NOT NULL DEFAULT '',
  evaluator        TEXT NOT NULL DEFAULT '',
  source_label     TEXT NOT NULL DEFAULT '',
  book_path        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_rijal_tradition ON rijal (tradition);
CREATE INDEX idx_rijal_category ON rijal (category);
CREATE TABLE canonical (
  canonical_id   INTEGER PRIMARY KEY,
  full_name      TEXT NOT NULL,
  kunya          TEXT NOT NULL DEFAULT '',
  nisba          TEXT NOT NULL DEFAULT '',
  tradition      TEXT NOT NULL DEFAULT '',
  death_year     INTEGER,
  birth_year     INTEGER,
  entry_count    INTEGER NOT NULL DEFAULT 1,
  source_count   INTEGER NOT NULL DEFAULT 0,
  teacher_count  INTEGER NOT NULL DEFAULT 0,
  student_count  INTEGER NOT NULL DEFAULT 0,
  merge_confidence REAL
);
CREATE INDEX idx_canonical_tradition ON canonical (tradition);
"""

_RIJAL_INSERT = """
INSERT INTO rijal
  (id, full_name, kunya, nisba, tradition, death_year, birth_year, category,
   teacher_count, student_count, reliability_term, reliability_grade,
   evaluator, source_label, book_path)
VALUES
  (:id, :full_name, :kunya, :nisba, :tradition, :death_year, :birth_year, :category,
   :teacher_count, :student_count, :reliability_term, :reliability_grade,
   :evaluator, :source_label, :book_path)
"""

_CANONICAL_INSERT = """
INSERT INTO canonical
  (canonical_id, full_name, kunya, nisba, tradition, death_year, birth_year,
   entry_count, source_count, teacher_count, student_count, merge_confidence)
VALUES
  (:canonical_id, :full_name, :kunya, :nisba, :tradition, :death_year, :birth_year,
   :entry_count, :source_count, :teacher_count, :student_count, :merge_confidence)
"""


def create_artifact(out: Path) -> sqlite3.Connection:
    """Create a fresh registry database at ``out`` and apply the schema."""
    if out.exists():
        out.unlink()
    con = sqlite3.connect(out)
    con.executescript(REGISTRY_SCHEMA)
    return con


def insert_rijal(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """Insert projected rijal rows (named dicts) into an open build connection."""
    con.executemany(_RIJAL_INSERT, rows)


def insert_canonical(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """Insert projected canonical rows (named dicts) into a build connection."""
    con.executemany(_CANONICAL_INSERT, rows)


def finalize(con: sqlite3.Connection) -> None:
    """Optimize the freshly built database (statistics + compaction)."""
    con.execute("ANALYZE")
    con.execute("VACUUM")
