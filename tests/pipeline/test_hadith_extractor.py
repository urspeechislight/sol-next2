"""Tests for the hadith narrator extractor and isnad-end detection.

Build minimal HADITH_TRANSMISSION spans with hand-placed ATTRIBUTION /
SPEECH_VERB_GENERIC patterns and assert the extractor slices the right narrator
names and that find_isnad_end caps at the matn boundary.
"""

from __future__ import annotations

from typing import Any

from backend.pipeline.config import load_config
from backend.pipeline.extractors.hadith import (
    AttributionCues,
    build_attribution_cues,
    filter_false_attributions,
    find_isnad_end,
    narrator_extractor,
)
from backend.pipeline.models import Pattern, Span

_CFG = load_config()
_PROXIMITY = _CFG.thresholds.isnad_chain_proximity_max
_GAP = _CFG.thresholds.isnad_chain_gap_max
_LOOKBACK = _CFG.thresholds.question_verb_lookback_chars
_LOOKAHEAD = _CFG.thresholds.narrator_disqualifier_lookahead_chars


def _pattern(pattern_id: str, text: str, pos: int) -> Pattern:
    """An ATTRIBUTION/speech-verb pattern covering [pos, pos+len(text))."""
    return Pattern(
        pattern_id=pattern_id, matched_text=text, char_start=pos, char_end=pos + len(text)
    )


def _span(text: str, patterns: list[Pattern], metadata: dict[str, Any] | None = None) -> Span:
    """A minimal paragraph span carrying the given patterns and metadata."""
    return Span(
        span_id="test_span",
        text=text,
        page_start=1,
        page_end=1,
        span_type="paragraph",
        patterns=patterns,
        metadata=metadata or {},
    )


def test_should_compile_attribution_cues_from_config() -> None:
    cues = build_attribution_cues(_CFG)
    assert isinstance(cues, AttributionCues)
    assert cues.question_verb_lookback == _LOOKBACK
    assert cues.disqualifier_lookahead == _LOOKAHEAD
    assert cues.ana_pronoun_regex is not None


def test_should_cap_isnad_at_terminal_speech_verb() -> None:
    text = "حدثنا محمد عن مالك قال رسول الله كذا"
    patterns = [
        _pattern("ATTRIBUTION", "حدثنا", text.index("حدثنا")),
        _pattern("ATTRIBUTION", "عن", text.index("عن")),
        _pattern("SPEECH_VERB_GENERIC", "قال", text.index("قال")),
    ]
    end = find_isnad_end(_span(text, patterns), _PROXIMITY, _GAP, build_attribution_cues(_CFG))
    assert end == text.index("قال")


def test_should_return_text_end_when_isnad_has_no_attributions() -> None:
    text = "هذا نص بلا إسناد"
    end = find_isnad_end(_span(text, []), _PROXIMITY, _GAP, build_attribution_cues(_CFG))
    assert end == len(text)


def test_should_extract_narrator_names_between_attributions() -> None:
    text = "حدثنا محمد بن إسماعيل عن يحيى بن سعيد قال رسول الله الخير"
    isnad_end = text.index("قال")
    patterns = [
        _pattern("ATTRIBUTION", "حدثنا", text.index("حدثنا")),
        _pattern("ATTRIBUTION", "عن", text.index("عن")),
        _pattern("SPEECH_VERB_GENERIC", "قال", isnad_end),
    ]
    entities = narrator_extractor(_span(text, patterns, metadata={"isnad_end": isnad_end}), _CFG)
    names = [entity.text for entity in entities]
    assert names == ["محمد بن إسماعيل", "يحيى بن سعيد"]
    assert all(entity.metadata["role_in_context"] == "narrator" for entity in entities)
    assert [entity.metadata["chain_position"] for entity in entities] == [0, 1]


def test_should_return_no_entities_when_span_has_no_attributions() -> None:
    text = "هذا متن بلا إسناد"
    assert narrator_extractor(_span(text, []), _CFG) == []


def test_should_drop_question_verb_prepositional_an() -> None:
    text = "سألت عن يمين القاضي"
    attr = _pattern("ATTRIBUTION", "عن", text.index("عن"))
    filtered = filter_false_attributions(_span(text, [attr]), [attr], build_attribution_cues(_CFG))
    assert filtered == []


def test_should_keep_chain_an_after_non_question_verb() -> None:
    text = "حدثنا عن مالك"
    attr = _pattern("ATTRIBUTION", "عن", text.index("عن"))
    filtered = filter_false_attributions(_span(text, [attr]), [attr], build_attribution_cues(_CFG))
    assert filtered == [attr]
