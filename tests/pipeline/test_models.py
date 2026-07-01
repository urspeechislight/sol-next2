"""Tests for the ported pipeline data models (phase 2-3 contract)."""

from __future__ import annotations

from backend.core.constants import HADITH__UNIT_ISNAD
from backend.pipeline.models import (
    HierarchyPath,
    Manuscript,
    Pattern,
    Span,
    Unit,
)


def _hierarchy() -> HierarchyPath:
    return HierarchyPath(path=[], path_ids=[], depth=0)


def test_should_collect_units_across_spans_when_assigned() -> None:
    span = Span(span_id="s1", text="x", page_start=1, page_end=1, span_type="p")
    span.units = [
        Unit(
            unit_id="u1",
            text_ar="chain",
            unit_type=HADITH__UNIT_ISNAD,
            behavior="HADITH_TRANSMISSION",
            span_id="s1",
            page_start=1,
            page_end=1,
            hierarchy=_hierarchy(),
        )
    ]
    manuscript = Manuscript(work_id="w", manifestation_id="m", spans=[span])
    assert [u.unit_type for u in manuscript.units] == [HADITH__UNIT_ISNAD]


def test_should_sort_patterns_by_offset_when_filtered_by_id() -> None:
    span = Span(span_id="s1", text="x", page_start=1, page_end=1, span_type="p")
    span.patterns = [
        Pattern(pattern_id="A", matched_text="a", char_start=5, char_end=6),
        Pattern(pattern_id="B", matched_text="b", char_start=0, char_end=1),
        Pattern(pattern_id="A", matched_text="a2", char_start=2, char_end=3),
    ]
    assert [p.char_start for p in span.patterns_by_id("A")] == [2, 5]
