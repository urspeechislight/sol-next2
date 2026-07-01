"""Read-only repository for the narrator registry — backed by ``data/registry.db``.

The served rijal + canonical queries (CENTRAL-005). Every statement is a fixed
literal — optional list filters use an always-bound sentinel
(``:param = '' OR column = :param``) so no SQL is ever built by interpolation.
The database is opened read-only + immutable at serve time, so it adds
negligible resident memory however large the corpus (rijal alone is 284k rows).
The DDL + INSERT helpers that materialize this artifact live in
``backend.build.rijal``.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from backend.core.constants import HTTP__DEFAULT_PAGE_SIZE
from backend.core.errors import ResourceNotFoundError
from backend.models.narrator import CanonicalEntry, RijalEntry
from backend.repositories._data_loader import open_ro_db

_DB_FILE = "registry.db"

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


def _connect() -> sqlite3.Connection:
    """Open the registry database read-only via the shared artifact opener."""
    return open_ro_db(
        _DB_FILE, "Narrator registry not built; run scripts/build_registry.py to materialize it"
    )


@dataclass(frozen=True, slots=True)
class RijalFilter:
    """Closed-set filters for a rijal listing query."""

    q: str = ""
    tradition: str = ""
    category: str = ""
    has_teachers: bool = False
    has_reliability: bool = False


def list_rijal(
    filters: RijalFilter,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[RijalEntry], int]:
    """Return ``(slice, total)`` of rijal entries matching the filters."""
    con = _connect()
    params: dict[str, Any] = {
        "q": filters.q,
        "qlike": f"%{filters.q}%",
        "tradition": filters.tradition,
        "category": filters.category,
        "has_teachers": int(filters.has_teachers),
        "has_reliability": int(filters.has_reliability),
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
