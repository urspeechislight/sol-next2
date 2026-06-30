"""Repository for the narrator registry — backed by ``data/registry.db``.

All SQL for the rijal + canonical corpora lives here (CENTRAL-005): the read
queries the API serves, and the write helpers ``scripts/build_registry.py``
uses to materialize the artifact from sol-next's projected rows. Every
statement is a fixed literal — optional list filters use an always-bound
sentinel (``:param = '' OR column = :param``) so no SQL is ever built by
interpolation. The database is opened read-only + immutable at serve time,
so it adds negligible resident memory however large the corpus (rijal alone
is 284k rows).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from backend.core.constants import HTTP__DEFAULT_PAGE_SIZE
from backend.core.errors import ResourceNotFoundError
from backend.models.narrator import CanonicalEntry, RijalEntry
from backend.repositories._data_loader import open_ro_db

_DB_FILE = "registry.db"

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

_RIJAL_FILTER = """
FROM rijal
WHERE (:q = '' OR full_name LIKE :qlike OR kunya LIKE :qlike OR nisba LIKE :qlike)
  AND (:tradition = '' OR tradition = :tradition)
  AND (:category = '' OR category = :category)
  AND (:has_teachers = 0 OR teacher_count > 0)
  AND (:has_reliability = 0 OR reliability_term <> '')
"""

_RIJAL_COUNT = "SELECT COUNT(*) " + _RIJAL_FILTER
_RIJAL_PAGE = "SELECT * " + _RIJAL_FILTER + " ORDER BY id LIMIT :limit OFFSET :offset"

_CANONICAL_FILTER = """
FROM canonical
WHERE (:q = '' OR full_name LIKE :qlike OR kunya LIKE :qlike OR nisba LIKE :qlike)
  AND (:merged_only = 0 OR entry_count > 1)
"""

_CANONICAL_COUNT = "SELECT COUNT(*) " + _CANONICAL_FILTER
_CANONICAL_PAGE = (
    "SELECT * " + _CANONICAL_FILTER + " ORDER BY canonical_id LIMIT :limit OFFSET :offset"
)


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


def _connect() -> sqlite3.Connection:
    """Open the registry database read-only via the shared artifact opener."""
    return open_ro_db(
        _DB_FILE, "Narrator registry not built; run scripts/build_registry.py to materialize it"
    )


def list_rijal(
    q: str = "",
    tradition: str = "",
    category: str = "",
    has_teachers: bool = False,
    has_reliability: bool = False,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[RijalEntry], int]:
    """Return ``(slice, total)`` of rijal entries matching the filters."""
    con = _connect()
    params: dict[str, Any] = {
        "q": q,
        "qlike": f"%{q}%",
        "tradition": tradition,
        "category": category,
        "has_teachers": int(has_teachers),
        "has_reliability": int(has_reliability),
    }
    total = int(con.execute(_RIJAL_COUNT, params).fetchone()[0])
    rows = con.execute(_RIJAL_PAGE, {**params, "limit": limit, "offset": offset}).fetchall()
    return [RijalEntry.model_validate(dict(r)) for r in rows], total


def get_rijal(entry_id: int) -> RijalEntry:
    """Return one rijal entry by id, or raise ``ResourceNotFoundError``."""
    row = _connect().execute("SELECT * FROM rijal WHERE id = :id", {"id": entry_id}).fetchone()
    if row is None:
        raise ResourceNotFoundError(kind="rijal", identifier=str(entry_id))
    return RijalEntry.model_validate(dict(row))


def list_canonical(
    q: str = "",
    merged_only: bool = False,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[CanonicalEntry], int]:
    """Return ``(slice, total)`` of canonical profiles matching the filters."""
    con = _connect()
    params: dict[str, Any] = {"q": q, "qlike": f"%{q}%", "merged_only": int(merged_only)}
    total = int(con.execute(_CANONICAL_COUNT, params).fetchone()[0])
    rows = con.execute(_CANONICAL_PAGE, {**params, "limit": limit, "offset": offset}).fetchall()
    return [CanonicalEntry.model_validate(dict(r)) for r in rows], total


def get_canonical(canonical_id: int) -> CanonicalEntry:
    """Return one canonical profile by id, or raise ``ResourceNotFoundError``."""
    row = (
        _connect()
        .execute("SELECT * FROM canonical WHERE canonical_id = :id", {"id": canonical_id})
        .fetchone()
    )
    if row is None:
        raise ResourceNotFoundError(kind="canonical", identifier=str(canonical_id))
    return CanonicalEntry.model_validate(dict(row))
