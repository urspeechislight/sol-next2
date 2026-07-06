"""Read-only repository for the dev extraction-inspection surface (``/api/dev``).

The near-raw span + unit + entity projection of the manuscript artifact
(``data/manuscript.db``) that a developer validates the pipeline with:
per-book coverage summaries, one page's rows with their JSON fields decoded,
and the entry-number audit that checks the extracted units against the
edition's own printed ordinals. The reader-serving projection of the same
artifact lives in ``repositories.manuscript``; unlike that path, everything
here fails loudly when the artifact is absent or the URN unknown — a
validator must see absence, not empty lists. CENTRAL-005 permits the read
SQL here.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from backend.core.constants import (
    ARTIFACT__MANUSCRIPT_DB,
    QURAN__MANIFESTATION_ID,
    QURAN__TITLE_AR,
    QURAN__TITLE_EN,
)
from backend.core.errors import ResourceNotFoundError
from backend.core.paths import data_path
from backend.models.extraction import (
    BehaviorCount,
    EntrySectionAudit,
    ExtractionBookSummary,
    ExtractionEntity,
    ExtractionEntryAudit,
    ExtractionPage,
    ExtractionPattern,
    ExtractionSpan,
    ExtractionUnit,
)
from backend.patterns import CompiledPattern, cached_compile
from backend.repositories import books as books_repo
from backend.repositories._data_loader import open_ro_db

_MISSING_HINT = (
    "Manuscript index not built; run scripts/build_manuscript_index.py to materialize it"
)

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
_NUMBERED_UNITS_QUERY = (
    "SELECT unit_id, hierarchy_path, "
    "CAST(json_extract(metadata, '$.entry_number') AS INTEGER) AS entry_number "
    "FROM unit WHERE manifestation_id = :urn "
    "AND json_extract(metadata, '$.entry_number') IS NOT NULL ORDER BY unit_id"
)

_HADITH_LEAF_REGEX: CompiledPattern = cached_compile(r"^hadith_\d+$")


def _manifestation_title(urn: str) -> tuple[str, str | None]:
    """The (Arabic, English) title for a manifestation present in the artifact.

    A catalog book carries its title in the catalog. The Qurʾān is a manifestation
    that is not a catalog book, so its canonical title is used instead. Any other
    URN absent from the catalog still raises ResourceNotFoundError — a stale
    artifact must be rebuilt, not partially listed.
    """
    if urn == QURAN__MANIFESTATION_ID:
        return QURAN__TITLE_AR, QURAN__TITLE_EN
    book = books_repo.get_book(urn)
    return book.title_ar, book.title_en


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
        title_ar, title_en = _manifestation_title(urn)
        summaries.append(
            ExtractionBookSummary(
                urn=urn,
                title_ar=title_ar,
                title_en=title_en,
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
    _require_known(con, book_urn)
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


def entry_audit(book_urn: str) -> ExtractionEntryAudit:
    """Check extracted units against the edition's printed ordinals, per section.

    Ordinals restart per section (bāb), so units group by their hierarchy path
    with the pipeline's per-hadith counter leaf stripped. Within each section
    the printed numbers should run consecutively from the first to the last:
    a missing ordinal is evidence extraction dropped or merged that entry, a
    duplicate that it split one. Every section is returned, in document order,
    so the clean ones vouch for coverage rather than being silently omitted.
    """
    con = _artifact()
    _require_known(con, book_urn)
    numbers_by_section: dict[tuple[str, ...], list[int]] = {}
    for row in con.execute(_NUMBERED_UNITS_QUERY, {"urn": book_urn}):
        path = [str(part) for part in json.loads(row["hierarchy_path"])]
        if path and _HADITH_LEAF_REGEX.match(path[-1]):
            path = path[:-1]
        numbers_by_section.setdefault(tuple(path), []).append(int(row["entry_number"]))
    rows = [_section_audit(section, numbers) for section, numbers in numbers_by_section.items()]
    return ExtractionEntryAudit(
        book_urn=book_urn,
        numbered_units=sum(row.units for row in rows),
        sections=len(rows),
        sections_with_anomalies=sum(1 for row in rows if row.missing or row.duplicates),
        missing_total=sum(len(row.missing) for row in rows),
        duplicate_total=sum(len(row.duplicates) for row in rows),
        rows=rows,
    )


def _section_audit(section: tuple[str, ...], numbers: list[int]) -> EntrySectionAudit:
    """Sequence-check one section's printed ordinals."""
    present = set(numbers)
    first = min(numbers)
    last = max(numbers)
    seen: set[int] = set()
    repeated: set[int] = set()
    for number in numbers:
        if number in seen:
            repeated.add(number)
        seen.add(number)
    return EntrySectionAudit(
        section=list(section),
        units=len(numbers),
        first=first,
        last=last,
        missing=[number for number in range(first, last + 1) if number not in present],
        duplicates=sorted(repeated),
    )


def _artifact() -> sqlite3.Connection:
    """Open the artifact for the dev surface, raising loudly when absent.

    ``repositories.manuscript.hadiths_for_page`` degrades to raw page text
    when the index is unbuilt (the reader carve-out documented there); the
    inspection surface has the opposite contract and 404s so absence is
    visible.
    """
    if not data_path(ARTIFACT__MANUSCRIPT_DB).exists():
        raise ResourceNotFoundError(kind="manuscript artifact", identifier=ARTIFACT__MANUSCRIPT_DB)
    return open_ro_db(ARTIFACT__MANUSCRIPT_DB, _MISSING_HINT)


def _require_known(con: sqlite3.Connection, book_urn: str) -> None:
    """Raise ResourceNotFoundError when the URN has no spans in the artifact."""
    if con.execute(_KNOWN_URN_QUERY, {"urn": book_urn}).fetchone() is None:
        raise ResourceNotFoundError(kind="extracted book", identifier=book_urn)


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
