"""Build layer: materialize the read-only manuscript span artifact.

DDL + INSERT helpers that build ``data/manuscript.db`` (the ``span`` table,
one row per segment-phase span) from a segmented Manuscript. This is the WRITE
side; the served span queries will live in ``backend.repositories.reader`` once
the reader is wired to serve structured spans. CENTRAL-005 permits the DDL/INSERT
SQL here. Structured fields (hierarchy, patterns, metadata) are JSON-encoded.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from backend.core.errors import SegmentError
from backend.pipeline.models import Manuscript, Pattern, Span

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
"""

_SPAN_INSERT = (
    "INSERT INTO span (span_id, manifestation_id, work_id, page_start, page_end, "
    "span_type, behavior, text_ar, footnote_text, hierarchy_path, hierarchy_path_ids, "
    "hierarchy_depth, patterns, metadata) "
    "VALUES (:span_id, :manifestation_id, :work_id, :page_start, :page_end, "
    ":span_type, :behavior, :text_ar, :footnote_text, :hierarchy_path, "
    ":hierarchy_path_ids, :hierarchy_depth, :patterns, :metadata)"
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
