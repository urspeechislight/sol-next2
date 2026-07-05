"""Pydantic DTOs for the dev extraction-inspection surface (``/api/dev``).

The near-raw projection of the manuscript artifact (span + unit + entity,
with their JSON-encoded structured fields decoded) that a developer or admin
reads to validate what segment+extract produced for a book. Deliberately
richer than the reader DTOs: the point is to see the pipeline's work —
behaviors, matched patterns, char anchors, provenance — not a curated shape.
"""

from __future__ import annotations

from pydantic import Field, JsonValue

from backend.models._base import FrozenModel


class ExtractionPattern(FrozenModel):
    """One segment-phase pattern match recorded on a span."""

    pattern_id: str = Field(description="Routing-table pattern id (config/sol.yaml).")
    matched_text: str = Field(description="The exact text the pattern matched.")
    char_start: int = Field(description="Match start offset within the span text.")
    char_end: int = Field(description="Match end offset within the span text.")


class ExtractionSpan(FrozenModel):
    """One segment-phase span as stored in the manuscript artifact."""

    span_id: str = Field(description="Stable span id (document order sorts correctly).")
    page_start: int = Field(description="First page the span covers.")
    page_end: int = Field(description="Last page the span covers.")
    span_type: str = Field(description="Structural kind (content, heading, ...).")
    behavior: str = Field(description="Routed behavior label (HADITH_TRANSMISSION, ...).")
    text_ar: str = Field(description="Arabic span text.")
    footnote_text: str | None = Field(
        default=None, description="Footnote block split off the span, when present."
    )
    hierarchy_path: list[str] = Field(description="TOC-anchored section path, root first.")
    hierarchy_depth: int = Field(description="Depth of the span in the section hierarchy.")
    patterns: list[ExtractionPattern] = Field(
        description="Every pattern match that fed the behavior routing."
    )
    metadata: dict[str, JsonValue] = Field(description="Segment-phase metadata, decoded.")


class ExtractionUnit(FrozenModel):
    """One extract-phase atomic unit (isnad, matn, hadith, ...)."""

    unit_id: str = Field(description="Stable unit id (document order sorts correctly).")
    span_id: str = Field(description="Owning span id.")
    page_start: int = Field(description="First page the unit covers.")
    page_end: int = Field(description="Last page the unit covers.")
    unit_type: str = Field(description="Atomic kind (isnad, matn, hadith, ...).")
    behavior: str = Field(description="Behavior label inherited from the owning span.")
    text_ar: str = Field(description="Arabic unit text.")
    metadata: dict[str, JsonValue] = Field(description="Extract-phase metadata, decoded.")


class ExtractionEntity(FrozenModel):
    """One extracted entity with its anchors, provenance, and evidence."""

    entity_id: str = Field(description="Stable entity id.")
    span_id: str = Field(description="Owning span id (back-references keep their own span).")
    entity_type: str = Field(description="Entity kind (PERSON, ...).")
    text_ar: str = Field(description="Arabic entity text.")
    char_start: int = Field(description="Anchor start offset within the owning span text.")
    char_end: int = Field(description="Anchor end offset within the owning span text.")
    confidence: float | None = Field(
        default=None, description="Extractor confidence, when the extractor scores one."
    )
    metadata: dict[str, JsonValue] = Field(description="Extractor metadata, decoded.")
    provenance: dict[str, JsonValue] = Field(
        description="Which extractor produced this entity, and how."
    )
    evidence: dict[str, JsonValue] = Field(
        description="Anchor evidence: the source span and offsets the claim rests on."
    )


class ExtractionPage(FrozenModel):
    """Everything the pipeline produced for the spans starting on one page."""

    book_urn: str = Field(description="Manifestation URN the page belongs to.")
    page_number: int = Field(description="1-based page number.")
    spans: list[ExtractionSpan] = Field(description="Spans starting on this page, in order.")
    units: list[ExtractionUnit] = Field(description="Units starting on this page, in order.")
    entities: list[ExtractionEntity] = Field(
        description="Entities anchored on this page, span order then char order."
    )


class BehaviorCount(FrozenModel):
    """How many units of one behavior a book carries."""

    behavior: str = Field(description="Behavior label.")
    units: int = Field(description="Unit count for this behavior.")


class ExtractionBookSummary(FrozenModel):
    """Coverage summary for one book present in the manuscript artifact."""

    urn: str = Field(description="Manifestation URN.")
    title_ar: str = Field(description="Arabic title from the catalog.")
    title_en: str | None = Field(default=None, description="English title, if present.")
    first_page: int = Field(description="Lowest page on which a span starts.")
    page_end: int = Field(description="Highest page any span reaches.")
    pages_with_spans: int = Field(description="Distinct pages on which a span starts.")
    spans: int = Field(description="Total spans extracted for this book.")
    units: int = Field(description="Total units extracted for this book.")
    entities: int = Field(description="Total entities extracted for this book.")
    behaviors: list[BehaviorCount] = Field(description="Unit counts per behavior, largest first.")
