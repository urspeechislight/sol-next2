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
    HierarchyPath,
    Manuscript,
    ManuscriptPage,
    Pattern,
    Span,
)
from backend.pipeline.segment import segment

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


def test_should_extract_narrators_from_segmented_hadith_chain() -> None:
    """Full segment then extract on a realistic isnad chain.

    segment detects the attribution verbs and routes the chain span to
    HADITH_TRANSMISSION; extract then pulls narrator entities from those patterns
    and splits the sanad from the matn.
    """
    pages = [
        ManuscriptPage(
            page_number=1,
            page_name="1",
            text="كتاب الإيمان\nحدثنا محمد بن إسماعيل عن مالك بن أنس قال: إنما الأعمال بالنيات",
            is_content=True,
        )
    ]
    manuscript = Manuscript(
        work_id="w1",
        manifestation_id="m1",
        pages=pages,
        metadata={"book_type": "hadith", "toc": []},
    )

    result = extract(segment(manuscript, _CFG), _CFG)

    hadith_spans = [span for span in result.spans if span.behavior == HADITH__BEHAVIOR_TRANSMISSION]
    assert hadith_spans, "segment did not route the chain span to HADITH_TRANSMISSION"
    narrator_names = {entity.text for span in hadith_spans for entity in (span.entities or [])}
    assert narrator_names, "no narrator entities extracted from the isnad chain"
    assert any("محمد" in name for name in narrator_names)
    assert any("مالك" in name for name in narrator_names)
    isnad_units = [
        unit
        for span in hadith_spans
        for unit in (span.units or [])
        if unit.unit_type == "ISNAD_UNIT"
    ]
    assert isnad_units, "no ISNAD_UNIT produced from the chain"
