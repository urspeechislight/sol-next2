"""Tests for the date-expression extractor (hijri years and lunar months).

It consumes the HIJRI_YEAR / LUNAR_MONTH patterns segment detected on a span and
emits the matching entities, anchored to the exact matched slice, with the hijri
year normalized to Western digits in metadata.
"""

from __future__ import annotations

from backend.core.constants import DATE__ENTITY_HIJRI_YEAR, DATE__ENTITY_LUNAR_MONTH
from backend.pipeline.config import load_config
from backend.pipeline.extractors.dates import DATE__YEAR_KEY, date_expression_extractor
from backend.pipeline.models import HierarchyPath, Pattern, Span

_CFG = load_config()


def _span(text: str, patterns: list[Pattern]) -> Span:
    return Span(
        span_id="s_date",
        text=text,
        page_start=1,
        page_end=1,
        span_type="paragraph",
        behavior="HISTORICAL_NARRATIVE",
        hierarchy=HierarchyPath(path=["x"], path_ids=["x"], depth=1),
        patterns=patterns,
        metadata={},
    )


def test_should_normalize_the_hijri_year_to_western_digits() -> None:
    """An Arabic-Indic year is stored normalized in metadata; the text stays raw."""
    text = "سنة ٥ هـ"
    pattern = Pattern(
        pattern_id=DATE__ENTITY_HIJRI_YEAR, matched_text=text, char_start=0, char_end=len(text)
    )
    entities = date_expression_extractor(_span(text, [pattern]), _CFG)
    assert len(entities) == 1
    assert entities[0].entity_type == DATE__ENTITY_HIJRI_YEAR
    assert entities[0].metadata[DATE__YEAR_KEY] == "5"
    assert text[entities[0].char_start : entities[0].char_end] == entities[0].text


def test_should_emit_a_lunar_month_from_its_pattern() -> None:
    """A lunar-month pattern becomes a LUNAR_MONTH entity anchored to its slice."""
    text = "رمضان"
    pattern = Pattern(
        pattern_id=DATE__ENTITY_LUNAR_MONTH, matched_text=text, char_start=0, char_end=len(text)
    )
    entities = date_expression_extractor(_span(text, [pattern]), _CFG)
    assert [e.entity_type for e in entities] == [DATE__ENTITY_LUNAR_MONTH]
    assert entities[0].text == "رمضان"


def test_should_drop_a_hijri_pattern_with_no_year_digits() -> None:
    """A HIJRI_YEAR match carrying no digits is dropped, not emitted year-less."""
    text = "سنة كذا"
    pattern = Pattern(
        pattern_id=DATE__ENTITY_HIJRI_YEAR, matched_text=text, char_start=0, char_end=len(text)
    )
    assert date_expression_extractor(_span(text, [pattern]), _CFG) == []


def test_should_ignore_unrelated_patterns() -> None:
    """A span whose patterns are not date patterns yields no date entities."""
    pattern = Pattern(pattern_id="ATTRIBUTION", matched_text="حدثنا", char_start=0, char_end=5)
    assert date_expression_extractor(_span("حدثنا فلان", [pattern]), _CFG) == []
