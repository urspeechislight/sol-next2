"""Read-only repository for the manuscript artifact (``data/manuscript.db``).

Serves the structured hadith data extracted in Phase 3: ``hadiths_for_page`` reads
the ``unit`` + ``entity`` tables and reshapes them into the reader's ``Hadith``
DTO — one Hadith per isnad/matn span, narrators projected from PERSON entities.
Returns ``[]`` when the artifact is absent so the reader serves raw page text
until the index is built. The DDL + INSERT helpers that materialize this artifact
live in ``backend.build.manuscript``; CENTRAL-005 permits the read SQL here.
Narrators carry their registry link (rijal_id / canonical_id) resolved at
build time; the reader fetches the linked biography from /api/rijal or
/api/canonical on demand. Romanized name and grade still await registry
romanization — name carries the Arabic form and grade is blank.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from backend.core.constants import (
    HADITH__ENTITY_PERSON,
    HADITH__UNIT_HADITH,
    HADITH__UNIT_ISNAD,
    HADITH__UNIT_MATN,
)
from backend.core.paths import data_path
from backend.models.reader import Hadith, Narrator
from backend.repositories._data_loader import open_ro_db

_DB_FILE = "manuscript.db"
_MISSING_HINT = (
    "Manuscript index not built; run scripts/build_manuscript_index.py to materialize it"
)
_BLANK_GRADE = ""
_DEFAULT_CHAIN_POSITION = 0

_UNIT_PAGE_QUERY = (
    "SELECT unit_id, span_id, unit_type, text_ar FROM unit "
    "WHERE manifestation_id = :urn AND page_start = :page"
)
_ENTITY_PAGE_QUERY = (
    "SELECT span_id, text_ar, metadata FROM entity "
    "WHERE manifestation_id = :urn AND page_start = :page AND entity_type = :entity_type"
)


@dataclass(frozen=True, slots=True)
class _UnitRow:
    """One fetched unit row — the fields the reshape needs."""

    unit_id: str
    span_id: str
    unit_type: str
    text_ar: str


@dataclass(frozen=True, slots=True)
class _EntityRow:
    """One fetched PERSON entity row with its narrator-projection fields."""

    span_id: str
    text_ar: str
    role_in_context: str
    chain_position: int
    rijal_id: int | None
    canonical_id: int | None


@dataclass(frozen=True, slots=True)
class _HadithDraft:
    """A hadith awaiting sequence-number assignment after document-order sort."""

    order_id: str
    isnad_ar: str
    matn_ar: str
    narrators: list[Narrator]


def hadiths_for_page(book_urn: str, page_number: int) -> list[Hadith]:
    """Return the extracted hadiths that begin on ``page_number``, else [].

    Returns [] when the manuscript index has not been built yet (so the reader
    serves raw page text) or when the page has no isnad/matn spans.
    """
    if not data_path(_DB_FILE).exists():
        return []
    con = open_ro_db(_DB_FILE, _MISSING_HINT)
    unit_rows = _fetch_unit_rows(con, book_urn, page_number)
    if not unit_rows:
        return []
    entity_rows = _fetch_entity_rows(con, book_urn, page_number)
    return _reshape_hadiths(unit_rows, entity_rows)


def _fetch_unit_rows(con: sqlite3.Connection, book_urn: str, page_number: int) -> list[_UnitRow]:
    """Fetch the page's unit rows projected into typed records."""
    params: dict[str, Any] = {"urn": book_urn, "page": page_number}
    rows = con.execute(_UNIT_PAGE_QUERY, params).fetchall()
    return [_unit_row(dict(row)) for row in rows]


def _fetch_entity_rows(
    con: sqlite3.Connection, book_urn: str, page_number: int
) -> list[_EntityRow]:
    """Fetch the page's PERSON entity rows projected into typed records."""
    params: dict[str, Any] = {
        "urn": book_urn,
        "page": page_number,
        "entity_type": HADITH__ENTITY_PERSON,
    }
    rows = con.execute(_ENTITY_PAGE_QUERY, params).fetchall()
    return [_entity_row(dict(row)) for row in rows]


def _unit_row(d: dict[str, Any]) -> _UnitRow:
    """Build a _UnitRow from a fetched dict."""
    return _UnitRow(
        unit_id=str(d["unit_id"]),
        span_id=str(d["span_id"]),
        unit_type=str(d["unit_type"]),
        text_ar=str(d["text_ar"]),
    )


def _entity_row(d: dict[str, Any]) -> _EntityRow:
    """Build a _EntityRow from a fetched dict, decoding the metadata JSON."""
    metadata: dict[str, Any] = json.loads(d["metadata"])
    link: dict[str, Any] = metadata.get("narrator_link") or {}
    origin = str(link.get("origin", ""))
    link_id = int(link["id"]) if "id" in link else None
    return _EntityRow(
        span_id=str(d["span_id"]),
        text_ar=str(d["text_ar"]),
        role_in_context=str(metadata.get("role_in_context", "")),
        chain_position=int(metadata.get("chain_position", _DEFAULT_CHAIN_POSITION)),
        rijal_id=link_id if origin == "rijal" else None,
        canonical_id=link_id if origin == "canonical" else None,
    )


def _reshape_hadiths(unit_rows: list[_UnitRow], entity_rows: list[_EntityRow]) -> list[Hadith]:
    """Group units + entities by span and build Hadith DTOs in document order."""
    units_by_span = _group_units_by_span(unit_rows)
    entities_by_span = _group_entities_by_span(entity_rows)
    drafts: list[_HadithDraft] = []
    for span_id, units in units_by_span.items():
        isnad = units.get(HADITH__UNIT_ISNAD)
        matn = units.get(HADITH__UNIT_MATN) or units.get(HADITH__UNIT_HADITH)
        order_unit = isnad if isnad is not None else matn
        if order_unit is None:
            continue
        narrators = _narrators_sorted(entities_by_span.get(span_id, []))
        drafts.append(
            _HadithDraft(
                order_id=order_unit.unit_id,
                isnad_ar=isnad.text_ar if isnad is not None else "",
                matn_ar=matn.text_ar if matn is not None else "",
                narrators=narrators,
            )
        )
    drafts.sort(key=lambda draft: draft.order_id)
    return [
        Hadith(
            n=index,
            isnad_ar=draft.isnad_ar,
            matn_ar=draft.matn_ar,
            narrators=draft.narrators,
        )
        for index, draft in enumerate(drafts, start=1)
    ]


def _group_units_by_span(unit_rows: list[_UnitRow]) -> dict[str, dict[str, _UnitRow]]:
    """Index unit rows by span_id then unit_type."""
    by_span: dict[str, dict[str, _UnitRow]] = {}
    for unit in unit_rows:
        by_span.setdefault(unit.span_id, {})[unit.unit_type] = unit
    return by_span


def _group_entities_by_span(entity_rows: list[_EntityRow]) -> dict[str, list[_EntityRow]]:
    """Index entity rows by span_id."""
    by_span: dict[str, list[_EntityRow]] = {}
    for entity in entity_rows:
        by_span.setdefault(entity.span_id, []).append(entity)
    return by_span


def _narrators_sorted(entities: list[_EntityRow]) -> list[Narrator]:
    """Project PERSON entities into Narrator DTOs ordered by chain position."""
    ordered = sorted(entities, key=lambda entity: entity.chain_position)
    return [
        Narrator(
            name=entity.text_ar,
            name_ar=entity.text_ar,
            role=entity.role_in_context,
            grade=_BLANK_GRADE,
            rijal_id=entity.rijal_id,
            canonical_id=entity.canonical_id,
        )
        for entity in ordered
    ]
