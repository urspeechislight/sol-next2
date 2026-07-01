"""End-to-end tests for the extract phase orchestrator.

Build a minimal Manuscript with a HADITH_TRANSMISSION span (behavior + hierarchy +
ATTRIBUTION/SPEECH_VERB patterns) and assert extract() computes isnad_end,
extracts narrator entities, and atomicizes into ISNAD + MATN units; plus a
whole_span behavior and the gazetteer-unavailable degraded mode.
"""

from __future__ import annotations

from backend.core.constants import HADITH__BEHAVIOR_GENERAL_PROSE, HADITH__BEHAVIOR_TRANSMISSION
from backend.pipeline.config import load_config
from backend.pipeline.extract import extract
from backend.pipeline.models import (
    DegradedMode,
    HierarchyPath,
    Manuscript,
    Pattern,
    Span,
)

_CFG = load_config()


def _attr(text: str, pos: int) -> Pattern:
    return Pattern(
        pattern_id="ATTRIBUTION", matched_text=text, char_start=pos, char_end=pos + len(text)
    )


def _speech(text: str, pos: int) -> Pattern:
    return Pattern(
        pattern_id="SPEECH_VERB_GENERIC",
        matched_text=text,
        char_start=pos,
        char_end=pos + len(text),
    )


def test_should_extract_narrators_and_split_sanad_matn() -> None:
    text = "حدثنا محمد بن إسماعيل عن يحيى بن سعيد قال رسول الله الخير"
    qala_pos = text.index("قال")
    span = Span(
        span_id="s1",
        text=text,
        page_start=1,
        page_end=1,
        span_type="paragraph",
        behavior=HADITH__BEHAVIOR_TRANSMISSION,
        hierarchy=HierarchyPath(path=["كتاب"], path_ids=["k1"], depth=1),
        patterns=[
            _attr("حدثنا", 0),
            _attr("عن", text.index("عن")),
            _speech("قال", qala_pos),
        ],
    )
    manuscript = Manuscript(work_id="w1", manifestation_id="m1", spans=[span])

    result = extract(manuscript, _CFG)

    units = result.spans[0].units
    assert units is not None
    assert [unit.unit_type for unit in units] == ["ISNAD_UNIT", "MATN_UNIT"]
    assert units[0].text_ar.endswith("يحيى بن سعيد")
    assert units[1].text_ar.startswith("قال")
    names = [entity.text for entity in result.spans[0].entities or []]
    assert names == ["محمد بن إسماعيل", "يحيى بن سعيد"]
    assert all(entity.entity_id.startswith("s1_e") for entity in result.spans[0].entities or [])


def test_should_atomicize_whole_span_into_single_unit() -> None:
    span = Span(
        span_id="s2",
        text="هذا تعليق للناشر",
        page_start=2,
        page_end=2,
        span_type="paragraph",
        behavior=HADITH__BEHAVIOR_GENERAL_PROSE,
        hierarchy=HierarchyPath(path=[], path_ids=[], depth=0),
        patterns=[],
    )
    manuscript = Manuscript(work_id="w1", manifestation_id="m1", spans=[span])

    result = extract(manuscript, _CFG)

    units = result.spans[0].units
    assert units is not None
    assert len(units) == 1
    assert units[0].unit_type == "PROSE_UNIT"
    assert result.spans[0].entities == []


def test_should_record_gazetteer_unavailable_when_gazetteer_empty() -> None:
    span = Span(
        span_id="s3",
        text="نص عام",
        page_start=1,
        page_end=1,
        span_type="paragraph",
        behavior=HADITH__BEHAVIOR_GENERAL_PROSE,
        hierarchy=HierarchyPath(path=[], path_ids=[], depth=0),
        patterns=[],
    )
    manuscript = Manuscript(work_id="w1", manifestation_id="m1", spans=[span])

    result = extract(manuscript, _CFG)

    assert DegradedMode.GAZETTEER_UNAVAILABLE in result.degraded_modes
    assert any(
        issue.issue_type is DegradedMode.GAZETTEER_UNAVAILABLE for issue in result.validation_issues
    )
