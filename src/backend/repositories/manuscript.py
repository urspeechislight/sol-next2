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

The dev extraction-inspection surface (``/api/dev``) reads the same artifact
through ``extraction_summaries`` / ``page_extraction`` below: the near-raw
span + unit + entity projection a developer validates the pipeline with.
Unlike the reader path, it fails loudly when the artifact is absent — a
validator must know there is nothing to validate.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from backend.core.constants import (
    ARTIFACT__MANUSCRIPT_DB,
    HADITH__ENTITY_PERSON,
    HADITH__ROLE_NARRATOR,
    HADITH__ROLE_RELATIVE_REF,
    HADITH__UNIT_HADITH,
    HADITH__UNIT_ISNAD,
    HADITH__UNIT_MATN,
    NARRATOR_LINK__ID_KEY,
    NARRATOR_LINK__METADATA_KEY,
    NARRATOR_LINK__ORIGIN_CANONICAL,
    NARRATOR_LINK__ORIGIN_KEY,
    NARRATOR_LINK__ORIGIN_RIJAL,
)
from backend.core.errors import ResourceNotFoundError
from backend.core.paths import data_path
from backend.models.extraction import (
    BehaviorCount,
    ExtractionBookSummary,
    ExtractionEntity,
    ExtractionPage,
    ExtractionPattern,
    ExtractionSpan,
    ExtractionUnit,
)
from backend.models.reader import Hadith, Narrator
from backend.repositories import books as books_repo
from backend.repositories._data_loader import open_ro_db

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
    "WHERE manifestation_id = :urn AND page_start = :page AND entity_type = :entity_type "
    "AND json_extract(metadata, '$.role_in_context') IN (:role_narrator, :role_relative)"
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
    if not data_path(ARTIFACT__MANUSCRIPT_DB).exists():
        return []
    con = open_ro_db(ARTIFACT__MANUSCRIPT_DB, _MISSING_HINT)
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
    """Fetch the page's chain-member PERSON rows projected into typed records.

    Chain members only: named narrators and kinship relative references, both
    positioned links in the isnad. Matn ``mention`` entities are people the
    hadith is about, not transmitters, and must not surface as narrators.
    """
    params: dict[str, Any] = {
        "urn": book_urn,
        "page": page_number,
        "entity_type": HADITH__ENTITY_PERSON,
        "role_narrator": HADITH__ROLE_NARRATOR,
        "role_relative": HADITH__ROLE_RELATIVE_REF,
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
    """Build a _EntityRow from a fetched dict, decoding the metadata JSON.

    The ``narrator_link`` shape is the write/read contract with
    ``build/narrator_link.py``; both sides consume the ``NARRATOR_LINK__*``
    constants so the key and origin tokens cannot drift apart.
    """
    metadata: dict[str, Any] = json.loads(d["metadata"])
    link: dict[str, Any] = metadata.get(NARRATOR_LINK__METADATA_KEY) or {}
    origin = str(link.get(NARRATOR_LINK__ORIGIN_KEY, ""))
    link_id = int(link[NARRATOR_LINK__ID_KEY]) if NARRATOR_LINK__ID_KEY in link else None
    return _EntityRow(
        span_id=str(d["span_id"]),
        text_ar=str(d["text_ar"]),
        role_in_context=str(metadata.get("role_in_context", "")),
        chain_position=int(metadata.get("chain_position", _DEFAULT_CHAIN_POSITION)),
        rijal_id=link_id if origin == NARRATOR_LINK__ORIGIN_RIJAL else None,
        canonical_id=link_id if origin == NARRATOR_LINK__ORIGIN_CANONICAL else None,
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


_SPAN_SUMMARY_QUERY = (
    "SELECT manifestation_id, COUNT(*) AS spans, MIN(page_start) AS first_page, "
    "MAX(page_end) AS page_end, COUNT(DISTINCT page_start) AS pages_with_spans "
    "FROM span GROUP BY manifestation_id"
)
_UNIT_COUNT_QUERY = "SELECT manifestation_id, COUNT(*) AS n FROM unit GROUP BY manifestation_id"
_ENTITY_COUNT_QUERY = "SELECT manifestation_id, COUNT(*) AS n FROM entity GROUP BY manifestation_id"
_BEHAVIOR_COUNT_QUERY = (
    "SELECT manifestation_id, behavior, COUNT(*) AS n FROM unit "
    "GROUP BY manifestation_id, behavior ORDER BY n DESC, behavior"
)
_KNOWN_URN_QUERY = "SELECT 1 FROM span WHERE manifestation_id = :urn LIMIT 1"
_SPAN_EXTRACTION_QUERY = (
    "SELECT span_id, page_start, page_end, span_type, behavior, text_ar, footnote_text, "
    "hierarchy_path, hierarchy_depth, patterns, metadata FROM span "
    "WHERE manifestation_id = :urn AND page_start = :page ORDER BY span_id"
)
_UNIT_EXTRACTION_QUERY = (
    "SELECT unit_id, span_id, page_start, page_end, unit_type, behavior, text_ar, metadata "
    "FROM unit WHERE manifestation_id = :urn AND page_start = :page ORDER BY unit_id"
)
_ENTITY_EXTRACTION_QUERY = (
    "SELECT entity_id, span_id, entity_type, text_ar, char_start, char_end, confidence, "
    "metadata, provenance, evidence FROM entity "
    "WHERE manifestation_id = :urn AND page_start = :page ORDER BY span_id, char_start"
)


def extraction_summaries() -> list[ExtractionBookSummary]:
    """Return one coverage summary per book in the artifact, URN-ordered.

    Titles come from the catalog: a URN present in the artifact but absent
    from the catalog raises ResourceNotFoundError — a stale artifact must be
    rebuilt, not partially listed.
    """
    con = _artifact()
    unit_counts = _counts_by_urn(con, _UNIT_COUNT_QUERY)
    entity_counts = _counts_by_urn(con, _ENTITY_COUNT_QUERY)
    behaviors: dict[str, list[BehaviorCount]] = {}
    for row in con.execute(_BEHAVIOR_COUNT_QUERY):
        urn = str(row["manifestation_id"])
        behaviors.setdefault(urn, []).append(
            BehaviorCount(behavior=str(row["behavior"]), units=int(row["n"]))
        )
    summaries: list[ExtractionBookSummary] = []
    for row in con.execute(_SPAN_SUMMARY_QUERY):
        urn = str(row["manifestation_id"])
        book = books_repo.get_book(urn)
        summaries.append(
            ExtractionBookSummary(
                urn=urn,
                title_ar=book.title_ar,
                title_en=book.title_en,
                first_page=int(row["first_page"]),
                page_end=int(row["page_end"]),
                pages_with_spans=int(row["pages_with_spans"]),
                spans=int(row["spans"]),
                units=unit_counts.get(urn, 0),
                entities=entity_counts.get(urn, 0),
                behaviors=behaviors.get(urn, []),
            )
        )
    return sorted(summaries, key=lambda summary: summary.urn)


def page_extraction(book_urn: str, page_number: int) -> ExtractionPage:
    """Return every span, unit, and entity starting on one page, near-raw.

    An empty page (no spans start there) is legitimate data and returns empty
    lists; an unknown URN raises ResourceNotFoundError instead.
    """
    con = _artifact()
    if con.execute(_KNOWN_URN_QUERY, {"urn": book_urn}).fetchone() is None:
        raise ResourceNotFoundError(kind="extracted book", identifier=book_urn)
    params: dict[str, Any] = {"urn": book_urn, "page": page_number}
    return ExtractionPage(
        book_urn=book_urn,
        page_number=page_number,
        spans=[_extraction_span(dict(row)) for row in con.execute(_SPAN_EXTRACTION_QUERY, params)],
        units=[_extraction_unit(dict(row)) for row in con.execute(_UNIT_EXTRACTION_QUERY, params)],
        entities=[
            _extraction_entity(dict(row)) for row in con.execute(_ENTITY_EXTRACTION_QUERY, params)
        ],
    )


def _artifact() -> sqlite3.Connection:
    """Open the artifact for the dev surface, raising loudly when absent.

    ``hadiths_for_page`` degrades to raw page text when the index is unbuilt
    (the reader carve-out documented there); the inspection surface has the
    opposite contract and 404s so absence is visible.
    """
    if not data_path(ARTIFACT__MANUSCRIPT_DB).exists():
        raise ResourceNotFoundError(kind="manuscript artifact", identifier=ARTIFACT__MANUSCRIPT_DB)
    return open_ro_db(ARTIFACT__MANUSCRIPT_DB, _MISSING_HINT)


def _counts_by_urn(con: sqlite3.Connection, query: str) -> dict[str, int]:
    """Run one GROUP BY manifestation_id COUNT query into a urn → count map."""
    return {str(row["manifestation_id"]): int(row["n"]) for row in con.execute(query)}


def _extraction_span(d: dict[str, Any]) -> ExtractionSpan:
    """Build an ExtractionSpan from a fetched row, decoding the JSON fields."""
    return ExtractionSpan(
        span_id=str(d["span_id"]),
        page_start=int(d["page_start"]),
        page_end=int(d["page_end"]),
        span_type=str(d["span_type"]),
        behavior=str(d["behavior"]),
        text_ar=str(d["text_ar"]),
        footnote_text=d["footnote_text"],
        hierarchy_path=json.loads(d["hierarchy_path"]),
        hierarchy_depth=int(d["hierarchy_depth"]),
        patterns=[ExtractionPattern(**pattern) for pattern in json.loads(d["patterns"])],
        metadata=json.loads(d["metadata"]),
    )


def _extraction_unit(d: dict[str, Any]) -> ExtractionUnit:
    """Build an ExtractionUnit from a fetched row, decoding the metadata JSON."""
    return ExtractionUnit(
        unit_id=str(d["unit_id"]),
        span_id=str(d["span_id"]),
        page_start=int(d["page_start"]),
        page_end=int(d["page_end"]),
        unit_type=str(d["unit_type"]),
        behavior=str(d["behavior"]),
        text_ar=str(d["text_ar"]),
        metadata=json.loads(d["metadata"]),
    )


def _extraction_entity(d: dict[str, Any]) -> ExtractionEntity:
    """Build an ExtractionEntity from a fetched row, decoding the JSON fields."""
    return ExtractionEntity(
        entity_id=str(d["entity_id"]),
        span_id=str(d["span_id"]),
        entity_type=str(d["entity_type"]),
        text_ar=str(d["text_ar"]),
        char_start=int(d["char_start"]),
        char_end=int(d["char_end"]),
        confidence=d["confidence"],
        metadata=json.loads(d["metadata"]),
        provenance=json.loads(d["provenance"]),
        evidence=json.loads(d["evidence"]),
    )
