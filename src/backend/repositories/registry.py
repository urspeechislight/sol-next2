"""Read-only repository for the narrator registry — backed by ``data/registry.db``.

The served narrator queries (CENTRAL-005). Every statement is a fixed
literal — optional list filters use an always-bound sentinel
(``:param = '' OR column = :param``) so no SQL is ever built by interpolation.
The database is opened read-only + immutable at serve time, so it adds
negligible resident memory however large the corpus (narrator alone is ~90k
rows). The DDL + extraction queries that materialize this artifact live in
``backend.build.rijal``.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Final

from pydantic import BaseModel

from backend.core.constants import (
    ARTIFACT__REGISTRY_DB,
    HTTP__DEFAULT_PAGE_SIZE,
    NARRATORS__GRAPH_MAX_NODES,
)
from backend.core.errors import ResourceNotFoundError
from backend.models.narrator import (
    NarratorAliasOut,
    NarratorDetail,
    NarratorEntry,
    NarratorGradeOut,
    NarratorGraph,
    NarratorGraphEdge,
    NarratorGraphNode,
)
from backend.patterns import normalize_narrator_name
from backend.repositories._data_loader import open_ro_db

MAX_GRAPH_NODES: Final[int] = NARRATORS__GRAPH_MAX_NODES

_NARRATOR_LIST_SELECT = """
SELECT n.id, n.primary_name_ar, COALESCE(n.primary_name_en, '') AS primary_name_en,
       COALESCE(n.kunya, '') AS kunya, COALESCE(n.nisba, '') AS nisba,
       COALESCE(n.tradition, '') AS tradition, n.birth_year_ah, n.death_year_ah,
       COALESCE(n.death_year_ce, '') AS death_year_ce,
       COALESCE(n.tabaqa, '') AS tabaqa, COALESCE(n.living_city, '') AS living_city,
       COALESCE(n.death_place, '') AS death_place, n.category,
       (SELECT COUNT(*) FROM narrator_alias a WHERE a.narrator_id = n.id) AS alias_count,
       (SELECT COUNT(DISTINCT e.from_id) FROM narrator_edge e WHERE e.to_id = n.id)
         AS teacher_count,
       (SELECT COUNT(DISTINCT e.to_id) FROM narrator_edge e WHERE e.from_id = n.id)
         AS student_count
"""

_NARRATOR_BY_ID = _NARRATOR_LIST_SELECT + " FROM narrator n WHERE n.id = :id"

_NARRATOR_FILTER = """
FROM narrator n
WHERE (:category = '' OR n.category = :category)
  AND (:tradition = '' OR n.tradition = :tradition)
  AND (:q = '' OR n.primary_name_ar LIKE :qraw
       OR EXISTS (SELECT 1 FROM narrator_alias a
                  WHERE a.narrator_id = n.id AND a.name_normalized LIKE :qnorm))
"""

_NARRATOR_COUNT = "SELECT COUNT(*) " + _NARRATOR_FILTER
_NARRATOR_PAGE = (
    _NARRATOR_LIST_SELECT + _NARRATOR_FILTER + " ORDER BY n.id LIMIT :limit OFFSET :offset"
)

_NARRATOR_EXISTS = "SELECT 1 FROM narrator WHERE id = :id"

_NARRATOR_NAME_BY_ID = (
    "SELECT primary_name_ar, primary_name_en, death_year_ah FROM narrator WHERE id = :id"
)

_ALIASES_BY_NARRATOR = """
SELECT name_ar, COALESCE(name_role, '') AS name_role, COALESCE(source_label, '') AS source_label
FROM narrator_alias WHERE narrator_id = :id ORDER BY id
"""

_GRADES_BY_NARRATOR = """
SELECT COALESCE(value_text, '') AS term, value_json, COALESCE(source_label, '') AS source_label
FROM narrator_claim WHERE narrator_id = :id AND claim_type = 'GRADE' ORDER BY id
"""

_STANCES_BY_NARRATOR = """
SELECT predicate, COALESCE(value_text, '') AS value_text
FROM narrator_claim WHERE narrator_id = :id AND claim_type = 'ALID_STANCE' ORDER BY id
"""

_TARJAMA_BY_NARRATOR = """
SELECT value_text FROM narrator_claim
WHERE narrator_id = :id AND claim_type = 'TARJAMA' AND value_text IS NOT NULL ORDER BY id
"""

_WALK_STUDENTS = """
WITH RECURSIVE walk(id, depth) AS (
  SELECT :root, 0
  UNION
  SELECT e.to_id, w.depth + 1
  FROM walk w JOIN narrator_edge e ON e.from_id = w.id
  WHERE w.depth < :depth
)
SELECT w.id, w.depth FROM walk w ORDER BY w.depth, w.id
"""

_WALK_TEACHERS = """
WITH RECURSIVE walk(id, depth) AS (
  SELECT :root, 0
  UNION
  SELECT e.from_id, w.depth + 1
  FROM walk w JOIN narrator_edge e ON e.to_id = w.id
  WHERE w.depth < :depth
)
SELECT w.id, w.depth FROM walk w ORDER BY w.depth, w.id
"""

_EDGES_STUDENTS = """
WITH RECURSIVE walk(id, depth) AS (
  SELECT :root, 0
  UNION
  SELECT e.to_id, w.depth + 1
  FROM walk w JOIN narrator_edge e ON e.from_id = w.id
  WHERE w.depth < :depth
)
SELECT e.from_id, e.to_id, e.source_label
FROM narrator_edge e
JOIN walk wf ON wf.id = e.from_id AND wf.depth < :depth
JOIN walk wt ON wt.id = e.to_id AND wt.depth = wf.depth + 1
ORDER BY e.from_id, e.to_id, e.source_label
"""

_EDGES_TEACHERS = """
WITH RECURSIVE walk(id, depth) AS (
  SELECT :root, 0
  UNION
  SELECT e.from_id, w.depth + 1
  FROM walk w JOIN narrator_edge e ON e.to_id = w.id
  WHERE w.depth < :depth
)
SELECT e.from_id, e.to_id, e.source_label
FROM narrator_edge e
JOIN walk wt ON wt.id = e.to_id AND wt.depth < :depth
JOIN walk wf ON wf.id = e.from_id AND wf.depth = wt.depth + 1
ORDER BY wf.depth, e.from_id, e.to_id, e.source_label
"""


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


@dataclass(frozen=True, slots=True)
class NarratorFilter:
    """Closed-set filters for a narrator listing query."""

    q: str = ""
    category: str = ""
    tradition: str = ""


def list_narrators(
    filters: NarratorFilter,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[NarratorEntry], int]:
    """Return ``(slice, total)`` of narrators matching the filters.

    ``q`` is a substring match against the folded alias names
    (``name_normalized``, the sol-next3 narrator fold: diacritics stripped,
    letter variants folded, nasab ابن collapsed to بن) and, as a second
    pass, the raw ``primary_name_ar`` — so an exact spelling of the pointed
    form still finds its narrator.
    """
    params: dict[str, Any] = {
        "q": filters.q,
        "qraw": f"%{filters.q}%",
        "qnorm": f"%{normalize_narrator_name(filters.q)}%",
        "category": filters.category,
        "tradition": filters.tradition,
    }
    return _paged_query(_NARRATOR_COUNT, _NARRATOR_PAGE, params, NarratorEntry, limit, offset)


def get_narrator(narrator_id: int) -> NarratorDetail:
    """Return one narrator's full served record, or raise ``ResourceNotFoundError``."""
    con = _connect()
    detail = con.execute(_NARRATOR_BY_ID, {"id": narrator_id}).fetchone()
    if detail is None:
        raise ResourceNotFoundError(kind="narrator", identifier=str(narrator_id))
    aliases = [
        NarratorAliasOut.model_validate(dict(row))
        for row in con.execute(_ALIASES_BY_NARRATOR, {"id": narrator_id})
    ]
    grades = [
        _grade_out(dict(row)) for row in con.execute(_GRADES_BY_NARRATOR, {"id": narrator_id})
    ]
    stances = [dict(row) for row in con.execute(_STANCES_BY_NARRATOR, {"id": narrator_id})]
    tarjama = [
        str(row["value_text"]) for row in con.execute(_TARJAMA_BY_NARRATOR, {"id": narrator_id})
    ]
    entry = NarratorEntry.model_validate(dict(detail))
    return NarratorDetail(
        **entry.model_dump(),
        aliases=aliases,
        grades=grades,
        stances=stances,
        tarjama=tarjama,
    )


def _grade_out(row: dict[str, Any]) -> NarratorGradeOut:
    """Build one grade record from a GRADE claim row, decoding its JSON payload."""
    payload: dict[str, Any] = json.loads(row["value_json"]) if row["value_json"] else {}
    locator = payload.get("source_locator")
    return NarratorGradeOut(
        term=str(row["term"]),
        tier=str(payload.get("normalized_tier") or ""),
        evaluator=str(payload.get("evaluator") or ""),
        source_label=str(row["source_label"]),
        source_book=str(payload.get("source_book") or ""),
        source_locator="" if locator is None else str(locator),
    )


def get_narrator_graph(narrator_id: int, direction: str, depth: int) -> NarratorGraph:
    """Return the breadth-limited teacher or student expansion around one narrator.

    A recursive CTE walks ``narrator_edge`` from the root (students follow
    teacher→student edges outward; teachers walk them inward), deduplicating
    each narrator at its shallowest depth. The walk is then capped at
    ``MAX_GRAPH_NODES`` (lowest depths first); a capped walk sets
    ``truncated=True`` and drops the edges whose endpoints fell outside the
    kept node set. Raises ``ResourceNotFoundError`` for an unknown root.
    """
    if direction not in ("students", "teachers"):
        raise ValueError(f"unknown graph direction: {direction!r}")
    con = _connect()
    if con.execute(_NARRATOR_EXISTS, {"id": narrator_id}).fetchone() is None:
        raise ResourceNotFoundError(kind="narrator", identifier=str(narrator_id))
    walk_sql = _WALK_STUDENTS if direction == "students" else _WALK_TEACHERS
    edge_sql = _EDGES_STUDENTS if direction == "students" else _EDGES_TEACHERS
    walk_params = {"root": narrator_id, "depth": depth}
    walk_rows = con.execute(walk_sql, walk_params).fetchall()
    truncated = len(walk_rows) > MAX_GRAPH_NODES
    kept = walk_rows[:MAX_GRAPH_NODES]
    kept_ids = {int(row["id"]) for row in kept}
    nodes: list[NarratorGraphNode] = []
    for row in kept:
        name_row = con.execute(_NARRATOR_NAME_BY_ID, {"id": int(row["id"])}).fetchone()
        if name_row is None:
            continue
        nodes.append(_graph_node(dict(name_row), int(row["id"]), int(row["depth"])))
    edges = [
        NarratorGraphEdge(
            from_id=int(row["from_id"]),
            to_id=int(row["to_id"]),
            source_label=str(row["source_label"]),
        )
        for row in con.execute(edge_sql, walk_params)
        if int(row["from_id"]) in kept_ids and int(row["to_id"]) in kept_ids
    ]
    return NarratorGraph(
        root_id=narrator_id,
        direction=direction,
        depth=depth,
        nodes=nodes,
        edges=edges,
        truncated=truncated,
    )


def _graph_node(name_row: dict[str, Any], narrator_id: int, depth: int) -> NarratorGraphNode:
    """Build one graph node from a name row plus its walk id and depth."""
    return NarratorGraphNode(
        id=narrator_id,
        primary_name_ar=str(name_row["primary_name_ar"]),
        primary_name_en=str(name_row["primary_name_en"] or ""),
        death_year_ah=(
            int(name_row["death_year_ah"]) if name_row["death_year_ah"] is not None else None
        ),
        depth=depth,
    )
