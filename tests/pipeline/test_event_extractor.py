"""Tests for the historical-event extractor.

Fixtures are real historical phrasings. The extractor must name a distinctive
event with its type and canonical id, keep an ambiguous name only in its event
frame (وقعة بدر but not the bare بدر), record a participation role when a marker
precedes (شهد … خيبر, استشهد بصفين), anchor each entity to its exact slice, and
stay silent outside the narrative genres.
"""

from __future__ import annotations

from backend.core.constants import ENTITY__NAME_KEY
from backend.pipeline.config import load_config
from backend.pipeline.extractors.events import (
    EVENT__ID_KEY,
    EVENT__ROLE_KEY,
    EVENT__TYPE_KEY,
    event_extractor,
)
from backend.pipeline.models import HierarchyPath, Span

_CFG = load_config()
_GENRE = "history-geography"


def _span(text: str, book_type: str) -> Span:
    return Span(
        span_id="s_event",
        text=text,
        page_start=1,
        page_end=1,
        span_type="paragraph",
        behavior="HISTORICAL_NARRATIVE",
        hierarchy=HierarchyPath(path=["x"], path_ids=["x"], depth=1),
        metadata={"book_type": book_type},
    )


def _events(text: str, book_type: str = _GENRE) -> list[dict[str, str]]:
    return [dict(e.metadata) for e in event_extractor(_span(text, book_type), _CFG)]


def test_should_name_a_distinctive_event_with_type_and_id() -> None:
    """A distinctive event name carries its type and canonical id."""
    events = _events("ثم كانت غزوة خيبر في السنة السابعة")
    assert events == [
        {ENTITY__NAME_KEY: "خيبر", EVENT__TYPE_KEY: "BATTLE", EVENT__ID_KEY: "khaybar"}
    ]


def test_should_keep_an_ambiguous_event_only_in_its_frame() -> None:
    """بدر is the battle after وقعة, but the bare word أحد ("one") is dropped."""
    assert _events("كانت وقعة بدر في رمضان") == [
        {ENTITY__NAME_KEY: "بدر", EVENT__TYPE_KEY: "BATTLE", EVENT__ID_KEY: "badr"}
    ]
    assert _events("لم يبق منهم أحد بعد ذلك") == []


def test_should_record_a_participation_role_when_a_marker_precedes() -> None:
    """A role marker in the preceding words stamps role + indicator on the event."""
    shahid = _events("وقد شهد فلان بن فلان خيبر مع النبي")
    assert shahid and shahid[0][EVENT__ROLE_KEY] == "shahid"
    qutila = _events("استشهد الصحابي بصفين مع علي")
    assert qutila and qutila[0][EVENT__ROLE_KEY] == "qutila"


def test_should_anchor_each_event_to_exact_offsets() -> None:
    """Every event's char window reproduces its surface exactly."""
    text = "شهد بدرا وأحدا والخندق مع رسول الله يوم بدر"
    span = _span(text, _GENRE)
    entities = event_extractor(span, _CFG)
    assert entities
    for entity in entities:
        assert text[entity.char_start : entity.char_end] == entity.text


def test_should_extract_nothing_outside_narrative_genres() -> None:
    """A fiqh or untyped book yields no events even with an event word."""
    assert event_extractor(_span("كانت وقعة بدر", "shia-fiqh-8th-century"), _CFG) == []
    assert event_extractor(_span("كانت وقعة بدر", "arabic-language-sciences"), _CFG) == []
