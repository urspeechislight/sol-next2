"""Tests for the hadith narrator extractor and isnad boundary detection.

Build minimal HADITH_TRANSMISSION spans with hand-placed ATTRIBUTION /
SPEECH_VERB_GENERIC patterns and assert the extractor slices the right narrator
names and that find_isnad_bounds windows the chain between the citation head
and the matn boundary.
"""

from __future__ import annotations

from typing import Any

from backend.pipeline.config import load_config
from backend.pipeline.extractors.hadith import narrator_extractor
from backend.pipeline.extractors.isnad_boundary import (
    AttributionCues,
    build_attribution_cues,
    filter_false_attributions,
    find_isnad_bounds,
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
    bounds = find_isnad_bounds(
        _span(text, patterns), _PROXIMITY, _GAP, build_attribution_cues(_CFG)
    )
    assert bounds == (0, text.index("قال"))


def test_should_return_text_end_when_isnad_has_no_attributions() -> None:
    text = "هذا نص بلا إسناد"
    bounds = find_isnad_bounds(_span(text, []), _PROXIMITY, _GAP, build_attribution_cues(_CFG))
    assert bounds == (0, len(text))


def test_should_start_isnad_after_citation_head_colon() -> None:
    text = (
        "2 - التوحيد ، عيون أخبار الرضا (ع) ، أمالي الصدوق : السناني ، عن الأسدي قال رسول الله كذا"
    )
    patterns = [
        _pattern("ATTRIBUTION", "عن", text.index("عن الأسدي")),
        _pattern("SPEECH_VERB_GENERIC", "قال", text.index("قال")),
    ]
    start, end = find_isnad_bounds(
        _span(text, patterns), _PROXIMITY, _GAP, build_attribution_cues(_CFG)
    )
    assert text[start:].startswith("السناني")
    assert end == text.index("قال")


def test_should_start_isnad_after_a_bare_numbered_marker() -> None:
    """A numbered hadith with no source citation still sheds its ordinal marker."""
    text = "2 - علي بن إبراهيم ، عن أبيه قال كذا"
    patterns = [
        _pattern("NUMBERED_ENTRY", "2 -", 0),
        _pattern("ATTRIBUTION", "عن", text.index("عن")),
        _pattern("SPEECH_VERB_GENERIC", "قال", text.index("قال")),
    ]
    start, _ = find_isnad_bounds(
        _span(text, patterns), _PROXIMITY, _GAP, build_attribution_cues(_CFG)
    )
    assert text[start:].startswith("علي بن إبراهيم")


def test_should_extract_head_narrator_before_first_attribution() -> None:
    text = "أمالي الصدوق : السناني ، عن الأسدي قال رسول الله كذا"
    isnad_end = text.index("قال")
    isnad_start = text.index("السناني")
    patterns = [
        _pattern("ATTRIBUTION", "عن", text.index("عن")),
        _pattern("SPEECH_VERB_GENERIC", "قال", isnad_end),
    ]
    entities = narrator_extractor(
        _span(text, patterns, metadata={"isnad_start": isnad_start, "isnad_end": isnad_end}),
        _CFG,
    )
    names = [entity.text for entity in entities]
    assert names == ["السناني", "الأسدي"]
    assert [entity.metadata["chain_position"] for entity in entities] == [0, 1]


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


def test_should_type_bare_kinship_reference_as_relative_reference() -> None:
    text = "حدثنا علي بن إبراهيم عن أبيه عن يحيى قال كذا"
    isnad_end = text.index("قال")
    patterns = [
        _pattern("ATTRIBUTION", "حدثنا", text.index("حدثنا")),
        _pattern("ATTRIBUTION", "عن", text.index("عن أبيه")),
        _pattern("ATTRIBUTION", "عن", text.index("عن يحيى")),
        _pattern("SPEECH_VERB_GENERIC", "قال", isnad_end),
    ]
    entities = narrator_extractor(_span(text, patterns, metadata={"isnad_end": isnad_end}), _CFG)
    by_text = {entity.text: entity for entity in entities}
    assert "أبيه" in by_text
    reference = by_text["أبيه"]
    assert reference.metadata["role_in_context"] == "relative_reference"
    assert reference.metadata["is_relative_reference"] is True
    assert "chain_position" in reference.metadata


def test_should_type_standalone_first_person_abi_as_relative_reference() -> None:
    text = "حدثنا أبي عن سعد قال كذا"
    isnad_end = text.index("قال")
    patterns = [
        _pattern("ATTRIBUTION", "حدثنا", text.index("حدثنا")),
        _pattern("ATTRIBUTION", "عن", text.index("عن سعد")),
        _pattern("SPEECH_VERB_GENERIC", "قال", isnad_end),
    ]
    entities = narrator_extractor(_span(text, patterns, metadata={"isnad_end": isnad_end}), _CFG)
    by_text = {entity.text: entity for entity in entities}
    assert by_text["أبي"].metadata["role_in_context"] == "relative_reference"
    assert by_text["سعد"].metadata["role_in_context"] == "narrator"


def test_should_not_split_a_kunya_headed_by_abi() -> None:
    text = "حدثنا محمد عن أبي عبد الله قال كذا"
    isnad_end = text.index("قال")
    patterns = [
        _pattern("ATTRIBUTION", "حدثنا", text.index("حدثنا")),
        _pattern("ATTRIBUTION", "عن", text.index("عن أبي عبد الله")),
        _pattern("SPEECH_VERB_GENERIC", "قال", isnad_end),
    ]
    entities = narrator_extractor(_span(text, patterns, metadata={"isnad_end": isnad_end}), _CFG)
    names = [entity.text for entity in entities]
    assert "أبي عبد الله" in names
    assert "عبد الله" not in names
    kunya = next(entity for entity in entities if entity.text == "أبي عبد الله")
    assert kunya.metadata["role_in_context"] == "narrator"


def test_should_strip_kinship_prefix_from_named_narrator() -> None:
    text = "حدثنا الإمام علي بن محمد عن أبيه محمد بن علي قال كذا"
    isnad_end = text.index("قال")
    patterns = [
        _pattern("ATTRIBUTION", "حدثنا", text.index("حدثنا")),
        _pattern("ATTRIBUTION", "عن", text.index("عن أبيه")),
        _pattern("SPEECH_VERB_GENERIC", "قال", isnad_end),
    ]
    entities = narrator_extractor(_span(text, patterns, metadata={"isnad_end": isnad_end}), _CFG)
    names = [entity.text for entity in entities]
    assert "محمد بن علي" in names
    named = next(entity for entity in entities if entity.text == "محمد بن علي")
    assert named.metadata["role_in_context"] == "narrator"
    assert named.metadata["relative_reference"] == "أبيه"
    assert text[named.char_start : named.char_end] == "محمد بن علي"


def test_should_strip_trailing_honorific_from_narrator_name() -> None:
    text = "حدثنا علي بن موسى ﵉ عن يحيى قال كذا"
    isnad_end = text.index("قال")
    patterns = [
        _pattern("ATTRIBUTION", "حدثنا", text.index("حدثنا")),
        _pattern("ATTRIBUTION", "عن", text.index("عن يحيى")),
        _pattern("SPEECH_VERB_GENERIC", "قال", isnad_end),
    ]
    entities = narrator_extractor(_span(text, patterns, metadata={"isnad_end": isnad_end}), _CFG)
    assert entities
    assert entities[0].text == "علي بن موسى"


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
