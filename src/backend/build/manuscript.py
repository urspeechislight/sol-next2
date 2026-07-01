"""Build layer: materialize the read-only manuscript artifact (span + entity + unit).

DDL + INSERT helpers that build ``data/manuscript.db`` from a segmented-then-
extracted Manuscript: the ``span`` table (one row per segment-phase span), the
``entity`` table (one row per extracted Entity), and the ``unit`` table (one row
per atomic Unit). This is the WRITE side; the served queries live in
``backend.repositories.manuscript``. CENTRAL-005 permits the DDL/INSERT SQL here.
Structured fields (hierarchy, patterns, metadata, provenance, evidence) are
JSON-encoded.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from backend.core.errors import ExtractError, SegmentError
from backend.pipeline.models import (
    Entity,
    EvidenceAnchor,
    ExtractionProvenance,
    Manuscript,
    Pattern,
    Span,
    Unit,
)

MANUSCRIPT_SCHEMA: str = """
DROP TABLE IF EXISTS span;
CREATE TABLE span (
  span_id            TEXT PRIMARY KEY,
  manifestation_id   TEXT NOT NULL,
  work_id            TEXT NOT NULL,
  page_start         INTEGER NOT NULL,
  page_end           INTEGER NOT NULL,
  span_type          TEXT NOT NULL,
  behavior           TEXT NOT NULL,
  text_ar            TEXT NOT NULL,
  footnote_text      TEXT,
  hierarchy_path     TEXT NOT NULL,
  hierarchy_path_ids TEXT NOT NULL,
  hierarchy_depth    INTEGER NOT NULL,
  patterns           TEXT NOT NULL,
  metadata           TEXT NOT NULL
);
CREATE INDEX idx_span_manifestation ON span (manifestation_id);
CREATE INDEX idx_span_page ON span (manifestation_id, page_start);

DROP TABLE IF EXISTS entity;
CREATE TABLE entity (
  entity_id          TEXT PRIMARY KEY,
  span_id            TEXT NOT NULL,
  manifestation_id   TEXT NOT NULL,
  page_start         INTEGER NOT NULL,
  page_end           INTEGER NOT NULL,
  entity_type        TEXT NOT NULL,
  text_ar            TEXT NOT NULL,
  char_start         INTEGER NOT NULL,
  char_end           INTEGER NOT NULL,
  metadata           TEXT NOT NULL,
  provenance         TEXT NOT NULL,
  evidence           TEXT NOT NULL,
  confidence         REAL
);
CREATE INDEX idx_entity_page ON entity (manifestation_id, page_start);
CREATE INDEX idx_entity_span ON entity (span_id);

DROP TABLE IF EXISTS unit;
CREATE TABLE unit (
  unit_id            TEXT PRIMARY KEY,
  span_id            TEXT NOT NULL,
  manifestation_id   TEXT NOT NULL,
  page_start         INTEGER NOT NULL,
  page_end           INTEGER NOT NULL,
  unit_type          TEXT NOT NULL,
  behavior           TEXT NOT NULL,
  text_ar            TEXT NOT NULL,
  hierarchy_path     TEXT NOT NULL,
  hierarchy_path_ids TEXT NOT NULL,
  hierarchy_depth    INTEGER NOT NULL,
  metadata           TEXT NOT NULL
);
CREATE INDEX idx_unit_page ON unit (manifestation_id, page_start);
CREATE INDEX idx_unit_span ON unit (span_id);
"""

_SPAN_INSERT = (
    "INSERT INTO span (span_id, manifestation_id, work_id, page_start, page_end, "
    "span_type, behavior, text_ar, footnote_text, hierarchy_path, hierarchy_path_ids, "
    "hierarchy_depth, patterns, metadata) "
    "VALUES (:span_id, :manifestation_id, :work_id, :page_start, :page_end, "
    ":span_type, :behavior, :text_ar, :footnote_text, :hierarchy_path, "
    ":hierarchy_path_ids, :hierarchy_depth, :patterns, :metadata)"
)
_ENTITY_INSERT = (
    "INSERT INTO entity (entity_id, span_id, manifestation_id, page_start, page_end, "
    "entity_type, text_ar, char_start, char_end, metadata, provenance, evidence, confidence) "
    "VALUES (:entity_id, :span_id, :manifestation_id, :page_start, :page_end, "
    ":entity_type, :text_ar, :char_start, :char_end, :metadata, :provenance, "
    ":evidence, :confidence)"
)
_UNIT_INSERT = (
    "INSERT INTO unit (unit_id, span_id, manifestation_id, page_start, page_end, "
    "unit_type, behavior, text_ar, hierarchy_path, hierarchy_path_ids, hierarchy_depth, "
    "metadata) "
    "VALUES (:unit_id, :span_id, :manifestation_id, :page_start, :page_end, "
    ":unit_type, :behavior, :text_ar, :hierarchy_path, :hierarchy_path_ids, "
    ":hierarchy_depth, :metadata)"
)


def create_span_store(out: Path) -> sqlite3.Connection:
    """Create a fresh manuscript span store at ``out`` and apply the schema."""
    if out.exists():
        out.unlink()
    con = sqlite3.connect(out)
    con.executescript(MANUSCRIPT_SCHEMA)
    return con


def span_rows(manuscript: Manuscript) -> list[dict[str, Any]]:
    """Project a segmented Manuscript's spans into span-table rows."""
    return [
        _span_row(manuscript.work_id, manuscript.manifestation_id, span)
        for span in manuscript.spans
    ]


def insert_spans(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """Insert projected span rows into the span table."""
    con.executemany(_SPAN_INSERT, rows)


def entity_rows(manuscript: Manuscript) -> list[dict[str, Any]]:
    """Project an extracted Manuscript's entities into entity-table rows.

    Iterates spans (not the flat manuscript.entities) so each entity row carries
    its OWNING span id — for isnad back-reference copies that is the back-ref
    span, while the anchored source span stays in the evidence JSON.
    """
    rows: list[dict[str, Any]] = []
    for span in manuscript.spans:
        for entity in span.entities or []:
            rows.append(_entity_row(span.span_id, manuscript.manifestation_id, entity))
    return rows


def unit_rows(manuscript: Manuscript) -> list[dict[str, Any]]:
    """Project an extracted Manuscript's atomic units into unit-table rows."""
    return [_unit_row(manuscript.manifestation_id, unit) for unit in manuscript.units]


def insert_entities(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """Insert projected entity rows into the entity table."""
    con.executemany(_ENTITY_INSERT, rows)


def insert_units(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """Insert projected unit rows into the unit table."""
    con.executemany(_UNIT_INSERT, rows)


def _span_row(work_id: str, manifestation_id: str, span: Span) -> dict[str, Any]:
    """Project one Span into a span-table row (JSON-encoding the structured fields).

    Raises SegmentError if the span lacks behavior/hierarchy — the writer only
    accepts post-segment manuscripts, so a None field means segment never ran.
    """
    behavior = span.behavior
    hierarchy = span.hierarchy
    if behavior is None or hierarchy is None:
        raise SegmentError(
            f"span {span.span_id} has no behavior/hierarchy; manuscript was not segmented"
        )
    return {
        "span_id": span.span_id,
        "manifestation_id": manifestation_id,
        "work_id": work_id,
        "page_start": span.page_start,
        "page_end": span.page_end,
        "span_type": span.span_type,
        "behavior": behavior,
        "text_ar": span.text,
        "footnote_text": span.footnote_text,
        "hierarchy_path": json.dumps(hierarchy.path, ensure_ascii=False),
        "hierarchy_path_ids": json.dumps(hierarchy.path_ids, ensure_ascii=False),
        "hierarchy_depth": hierarchy.depth,
        "patterns": json.dumps(_pattern_rows(span.patterns), ensure_ascii=False),
        "metadata": json.dumps(span.metadata, ensure_ascii=False),
    }


def _pattern_rows(patterns: list[Pattern]) -> list[dict[str, Any]]:
    """Project a span's patterns into JSON-serializable dicts."""
    return [
        {
            "pattern_id": pattern.pattern_id,
            "matched_text": pattern.matched_text,
            "char_start": pattern.char_start,
            "char_end": pattern.char_end,
        }
        for pattern in patterns
    ]


def _entity_row(span_id: str, manifestation_id: str, entity: Entity) -> dict[str, Any]:
    """Project one Entity into an entity-table row (JSON-encoding the structured fields).

    span_id is the OWNING span (the span whose entities list holds it); the anchor
    span recorded in evidence may differ for isnad back-reference copies. Raises
    ExtractError when provenance/evidence is missing — create_entity always sets
    both, so a None means extract never ran on this entity.
    """
    provenance = entity.provenance
    evidence = entity.evidence
    if provenance is None or evidence is None:
        raise ExtractError(
            f"entity {entity.entity_id} has no provenance/evidence; manuscript was not extracted"
        )
    return {
        "entity_id": entity.entity_id,
        "span_id": span_id,
        "manifestation_id": manifestation_id,
        "page_start": evidence.page_start,
        "page_end": evidence.page_end,
        "entity_type": entity.entity_type,
        "text_ar": entity.text,
        "char_start": entity.char_start,
        "char_end": entity.char_end,
        "metadata": json.dumps(entity.metadata, ensure_ascii=False),
        "provenance": json.dumps(_provenance_row(provenance), ensure_ascii=False),
        "evidence": json.dumps(_evidence_row(evidence), ensure_ascii=False),
        "confidence": entity.confidence,
    }


def _unit_row(manifestation_id: str, unit: Unit) -> dict[str, Any]:
    """Project one Unit into a unit-table row (JSON-encoding the structured fields)."""
    return {
        "unit_id": unit.unit_id,
        "span_id": unit.span_id,
        "manifestation_id": manifestation_id,
        "page_start": unit.page_start,
        "page_end": unit.page_end,
        "unit_type": unit.unit_type,
        "behavior": unit.behavior,
        "text_ar": unit.text_ar,
        "hierarchy_path": json.dumps(unit.hierarchy.path, ensure_ascii=False),
        "hierarchy_path_ids": json.dumps(unit.hierarchy.path_ids, ensure_ascii=False),
        "hierarchy_depth": unit.hierarchy.depth,
        "metadata": json.dumps(unit.metadata, ensure_ascii=False),
    }


def _provenance_row(provenance: ExtractionProvenance) -> dict[str, Any]:
    """Project an ExtractionProvenance into a JSON-serializable dict."""
    return {
        "extractor_id": provenance.extractor_id,
        "phase": provenance.phase,
        "pattern_ids": provenance.pattern_ids,
    }


def _evidence_row(evidence: EvidenceAnchor) -> dict[str, Any]:
    """Project an EvidenceAnchor into a JSON-serializable dict."""
    return {
        "span_id": evidence.span_id,
        "page_start": evidence.page_start,
        "page_end": evidence.page_end,
        "hierarchy_path": evidence.hierarchy.path,
        "hierarchy_path_ids": evidence.hierarchy.path_ids,
        "hierarchy_depth": evidence.hierarchy.depth,
        "context_before": evidence.context_before,
        "context_after": evidence.context_after,
    }

