"""Read-only repository for the narrator registry — backed by ``data/registry.db``.

The served rijal + person queries (CENTRAL-005). Every statement is a fixed
literal — optional list filters use an always-bound sentinel
(``:param = '' OR column = :param``) so no SQL is ever built by interpolation.
The database is opened read-only + immutable at serve time, so it adds
negligible resident memory however large the corpus (rijal alone is 284k rows).
The DDL + INSERT helpers that materialize this artifact live in
``backend.build.rijal`` (rijal) and ``backend.build.authority`` (person).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from backend.core.constants import ARTIFACT__REGISTRY_DB, HTTP__DEFAULT_PAGE_SIZE
from backend.core.errors import ResourceNotFoundError
from backend.models.narrator import CanonicalEntry, PersonEdge, PersonEntry, PersonEvent, RijalEntry
from backend.repositories._data_loader import open_ro_db

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

_PERSON_FILTER = """
FROM person
WHERE (:q = '' OR full_name LIKE :qlike OR kunya LIKE :qlike OR nisba LIKE :qlike
        OR name_variants LIKE :qlike)
  AND (:tradition = '' OR tradition = :tradition)
  AND (:stance = '' OR stance = :stance)
  AND (:confidence = '' OR confidence = :confidence)
  AND (:has_events = 0 OR event_count > 0)
"""

_PERSON_COUNT = "SELECT COUNT(*) " + _PERSON_FILTER
_PERSON_PAGE = (
    "SELECT * " + _PERSON_FILTER + " ORDER BY n_sources DESC, person_id LIMIT :limit OFFSET :offset"
)

_PERSON_EDGES = (
    "SELECT relation, name, other_person_id FROM person_edge "
    "WHERE person_id = :id ORDER BY relation, name"
)
_PERSON_EVENTS = (
    "SELECT event, event_type, year_ah, role FROM person_event "
    "WHERE person_id = :id ORDER BY year_ah"
)


def _connect() -> sqlite3.Connection:
    """Open the registry database read-only via the shared artifact opener."""
    return open_ro_db(
        ARTIFACT__REGISTRY_DB,
        "Narrator registry not built; run scripts/build_registry.py to materialize it",
    )


def _paged_query[M: BaseModel](
    count_sql: str,
    page_sql: str,
    params: dict[str, Any],
    model: type[M],
    limit: int,
    offset: int,
) -> tuple[list[M], int]:
    """Count + page + validate: the one (slice, total) shape over registry tables."""
    con = _connect()
    total = int(con.execute(count_sql, params).fetchone()[0])
    rows = con.execute(page_sql, {**params, "limit": limit, "offset": offset}).fetchall()
    return [model.model_validate(dict(r)) for r in rows], total


def _get_one[M: BaseModel](sql: str, key: int, model: type[M], kind: str) -> M:
    """Fetch one row by id and validate it, or raise ``ResourceNotFoundError``."""
    row = _connect().execute(sql, {"id": key}).fetchone()
    if row is None:
        raise ResourceNotFoundError(kind=kind, identifier=str(key))
    return model.model_validate(dict(row))


def _list_by_id[M: BaseModel](sql: str, key: int, model: type[M]) -> list[M]:
    """Fetch every row keyed to one id and validate them (a person's edges or events)."""
    rows = _connect().execute(sql, {"id": key}).fetchall()
    return [model.model_validate(dict(r)) for r in rows]


@dataclass(frozen=True, slots=True)
class RijalFilter:
    """Closed-set filters for a rijal listing query."""

    q: str = ""
    tradition: str = ""
    category: str = ""
    has_teachers: bool = False
    has_reliability: bool = False


@dataclass(frozen=True, slots=True)
class PersonFilter:
    """Closed-set filters for a person listing query."""

    q: str = ""
    tradition: str = ""
    stance: str = ""
    confidence: str = ""
    has_events: bool = False


def list_rijal(
    filters: RijalFilter,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[RijalEntry], int]:
    """Return ``(slice, total)`` of rijal entries matching the filters."""
    params: dict[str, Any] = {
        "q": filters.q,
        "qlike": f"%{filters.q}%",
        "tradition": filters.tradition,
        "category": filters.category,
        "has_teachers": int(filters.has_teachers),
        "has_reliability": int(filters.has_reliability),
    }
    return _paged_query(_RIJAL_COUNT, _RIJAL_PAGE, params, RijalEntry, limit, offset)


def get_rijal(entry_id: int) -> RijalEntry:
    """Return one rijal entry by id, or raise ``ResourceNotFoundError``."""
    return _get_one("SELECT * FROM rijal WHERE id = :id", entry_id, RijalEntry, "rijal")


def list_canonical(
    q: str = "",
    merged_only: bool = False,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[CanonicalEntry], int]:
    """Return ``(slice, total)`` of canonical profiles matching the filters."""
    params: dict[str, Any] = {"q": q, "qlike": f"%{q}%", "merged_only": int(merged_only)}
    return _paged_query(_CANONICAL_COUNT, _CANONICAL_PAGE, params, CanonicalEntry, limit, offset)


def get_canonical(canonical_id: int) -> CanonicalEntry:
    """Return one canonical profile by id, or raise ``ResourceNotFoundError``."""
    return _get_one(
        "SELECT * FROM canonical WHERE canonical_id = :id",
        canonical_id,
        CanonicalEntry,
        "canonical",
    )


def list_person(
    filters: PersonFilter,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[PersonEntry], int]:
    """Return ``(slice, total)`` of enriched persons matching the filters."""
    params: dict[str, Any] = {
        "q": filters.q,
        "qlike": f"%{filters.q}%",
        "tradition": filters.tradition,
        "stance": filters.stance,
        "confidence": filters.confidence,
        "has_events": int(filters.has_events),
    }
    return _paged_query(_PERSON_COUNT, _PERSON_PAGE, params, PersonEntry, limit, offset)


def get_person(person_id: int) -> PersonEntry:
    """Return one enriched person by id, or raise ``ResourceNotFoundError``."""
    return _get_one("SELECT * FROM person WHERE person_id = :id", person_id, PersonEntry, "person")


def get_person_edges(person_id: int) -> list[PersonEdge]:
    """Return a person's teacher/student relations (linked to a person id when known)."""
    return _list_by_id(_PERSON_EDGES, person_id, PersonEdge)


def get_person_events(person_id: int) -> list[PersonEvent]:
    """Return the historical events attributed to a person."""
    return _list_by_id(_PERSON_EVENTS, person_id, PersonEvent)
