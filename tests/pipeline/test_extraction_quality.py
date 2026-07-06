"""Extraction-quality regression tests on a real Bihar al-Anwar hadith.

The fixture is the hadith opening Bihar vol 5 page 6 (iz32WsFJ_05_s0008), the
span whose extraction defects drove the kinship/citation-head/mention fixes:
a Majlisi citation head before the chain, a head narrator with no leading
attribution verb, two kinship-prefixed narrators, a trailing honorific, and
three persons appearing only in the matn.
"""

from __future__ import annotations

from backend.pipeline.config import load_config
from backend.pipeline.extract import extract
from backend.pipeline.models import Entity, HierarchyPath, Manuscript, Pattern, Span, Unit
from backend.pipeline.vocab import HADITH__BEHAVIOR_TRANSMISSION

_CFG = load_config()

_TEXT = (
    "2 - التوحيد ، عيون أخبار الرضا (ع) ، أمالي الصدوق : السناني ، عن الأسدي ، "
    "عن عبد العظيم الحسني ، عن الإمام علي بن محمد ، عن أبيه محمد بن علي ، "
    "عن أبيه الرضا علي بن موسى ﵉ قال : خرج أبو حنيفة ذات يوم من عند الصادق ﵇ "
    "فاستقبله موسى بن جعفر ﵇ فقال له : يا غلام ممن المعصية"
)
_CITATION_HEAD = "2 - التوحيد ، عيون أخبار الرضا (ع) ، أمالي الصدوق :"
_CHAIN_ATTRIBUTION_ANCHORS = (
    "عن الأسدي",
    "عن عبد العظيم",
    "عن الإمام",
    "عن أبيه محمد",
    "عن أبيه الرضا",
)


def _pattern(pattern_id: str, matched: str, pos: int) -> Pattern:
    return Pattern(
        pattern_id=pattern_id, matched_text=matched, char_start=pos, char_end=pos + len(matched)
    )


def _extracted() -> tuple[list[Unit], list[Entity]]:
    """Run extract() over the fixture span; return its (units, entities)."""
    patterns = [
        _pattern("ATTRIBUTION", "عن", _TEXT.index(anchor)) for anchor in _CHAIN_ATTRIBUTION_ANCHORS
    ]
    patterns.append(_pattern("SPEECH_VERB_GENERIC", "قال", _TEXT.index("قال :")))
    patterns.append(_pattern("NUMBERED_ENTRY", "2 -", 0))
    span = Span(
        span_id="s_bihar_p6",
        text=_TEXT,
        page_start=6,
        page_end=6,
        span_type="paragraph",
        behavior=HADITH__BEHAVIOR_TRANSMISSION,
        hierarchy=HierarchyPath(path=["باب"], path_ids=["b1"], depth=1),
        patterns=patterns,
    )
    manuscript = Manuscript(work_id="w1", manifestation_id="m1", spans=[span])
    result = extract(manuscript, _CFG)
    assert result.spans[0].units is not None
    assert result.spans[0].entities is not None
    return result.spans[0].units, result.spans[0].entities


def test_should_keep_citation_head_out_of_the_isnad_unit() -> None:
    """The ordinal + source works stay off the chain text and ride as metadata."""
    units, _ = _extracted()
    isnad = units[0]
    assert isnad.unit_type == "ISNAD_UNIT"
    assert isnad.text_ar.startswith("السناني")
    assert isnad.metadata["citation_head"] == _CITATION_HEAD


def test_should_materialize_the_printed_entry_number() -> None:
    """The edition's ordinal lands as a typed field beside the citation head."""
    units, _ = _extracted()
    assert units[0].metadata["entry_number"] == 2


def test_should_extract_the_head_narrator_before_the_first_attribution() -> None:
    """السناني opens the chain even though no transmission verb precedes it."""
    _, entities = _extracted()
    narrators = [e for e in entities if e.metadata["role_in_context"] == "narrator"]
    assert narrators
    assert narrators[0].text == "السناني"
    assert narrators[0].metadata["chain_position"] == 0


def test_should_strip_kinship_prefix_and_honorific_from_named_narrators() -> None:
    """عن أبيه محمد بن علي yields the name alone; the ﵉ salutation is not a token."""
    _, entities = _extracted()
    by_text = {e.text: e for e in entities}
    assert "محمد بن علي" in by_text
    assert by_text["محمد بن علي"].metadata["relative_reference"] == "أبيه"
    assert "الرضا علي بن موسى" in by_text
    assert by_text["الرضا علي بن موسى"].metadata["relative_reference"] == "أبيه"
    assert not any("﵉" in text or "أبيه" in text for text in by_text)


def test_should_extract_matn_person_mentions() -> None:
    """The people the hadith is about surface as mention entities, not narrators."""
    _, entities = _extracted()
    mentions = {e.text for e in entities if e.metadata["role_in_context"] == "mention"}
    assert {"أبو حنيفة", "موسى بن جعفر", "الصادق"} <= mentions


def test_should_anchor_mentions_to_their_matn_offsets() -> None:
    """Each mention's char window reproduces its text, inside the matn region."""
    _, entities = _extracted()
    matn_start = _TEXT.index("خرج")
    for entity in entities:
        if entity.metadata["role_in_context"] != "mention":
            continue
        assert _TEXT[entity.char_start : entity.char_end] == entity.text
        assert entity.char_start >= matn_start


def _extract_one_span(text: str, attribution_anchors: tuple[str, ...], qala_anchor: str) -> Span:
    """Run extract() over one hadith span built from anchor substrings."""
    patterns = [_pattern("ATTRIBUTION", "عن", text.index(anchor)) for anchor in attribution_anchors]
    patterns.append(_pattern("SPEECH_VERB_GENERIC", "قال", text.index(qala_anchor)))
    span = Span(
        span_id="s_edge",
        text=text,
        page_start=1,
        page_end=1,
        span_type="paragraph",
        behavior=HADITH__BEHAVIOR_TRANSMISSION,
        hierarchy=HierarchyPath(path=["باب"], path_ids=["b1"], depth=1),
        patterns=patterns,
    )
    manuscript = Manuscript(work_id="w1", manifestation_id="m1", spans=[span])
    return extract(manuscript, _CFG).spans[0]


def test_should_split_kinship_prefix_across_a_line_break() -> None:
    """Page text keeps its newlines; عن أبيه\\nيزيد still splits token from name."""
    text = "الحسين بن أحمد ، عن أبيه\nيزيد بن سلام قال : سألت رسول الله"
    span = _extract_one_span(text, ("عن أبيه",), "قال :")
    by_text = {e.text: e for e in span.entities or []}
    assert "يزيد بن سلام" in by_text
    assert by_text["يزيد بن سلام"].metadata["relative_reference"] == "أبيه"
    assert not any(text.startswith("أبيه") for text in by_text)


def test_should_end_a_name_at_a_mid_slice_honorific() -> None:
    """The salutation follows a complete name: the candidate never runs past ﵉."""
    text = "محمد بن يحيى ، عن علي بن محمد العسكري ﵉ في رسالته إلى أهل الأهواز قال : كذا"
    span = _extract_one_span(text, ("عن علي",), "قال :")
    names = [e.text for e in span.entities or []]
    assert "علي بن محمد العسكري" in names
    assert not any("﵉" in name or "رسالته" in name for name in names)


_BACKREF_ROOT_TEXT = (
    "1 - التوحيد : أبي ، عن سعد بن عبد الله ، عن ابن عيسى قال : قال الصادق كذا وكذا"
)
_BACKREF_MID_TEXT = "2 - التوحيد : بهذا الاسناد ، عن جميل بن دراج قال : سمعت خبرا آخر عنه"
_BACKREF_TAIL_TEXT = "3 - التوحيد : وبهذا الاسناد قال : وروي في معناه خبر ثالث"


def _hadith_span(span_id: str, text: str, anchors: tuple[str, ...], qala: str) -> Span:
    """One HADITH_TRANSMISSION span with attribution patterns at the anchors."""
    patterns = [_pattern("ATTRIBUTION", "عن", text.index(anchor)) for anchor in anchors]
    patterns.append(_pattern("SPEECH_VERB_GENERIC", "قال", text.index(qala)))
    patterns.append(_pattern("NUMBERED_ENTRY", text[:3], 0))
    return Span(
        span_id=span_id,
        text=text,
        page_start=1,
        page_end=1,
        span_type="paragraph",
        behavior=HADITH__BEHAVIOR_TRANSMISSION,
        hierarchy=HierarchyPath(path=["باب"], path_ids=["b1"], depth=1),
        patterns=patterns,
    )


def _backref_chain() -> Manuscript:
    """Root hadith with a literal isnad, then two chained back-references."""
    root = _hadith_span("A", _BACKREF_ROOT_TEXT, ("عن سعد", "عن ابن عيسى"), "قال :")
    mid = _hadith_span("B", _BACKREF_MID_TEXT, ("عن جميل",), "قال :")
    mid.metadata = {"isnad_back_ref": True, "refers_to_span_id": "A"}
    tail = _hadith_span("C", _BACKREF_TAIL_TEXT, (), "قال :")
    tail.metadata = {"isnad_back_ref": True, "refers_to_span_id": "B"}
    manuscript = Manuscript(work_id="w1", manifestation_id="m1", spans=[root, mid, tail])
    return extract(manuscript, _CFG)


def _pointer_unit(span: Span) -> Unit:
    """The isnad-bearing unit the back-reference pointers ride on."""
    assert span.units
    for unit in span.units:
        if unit.unit_type == "ISNAD_UNIT":
            return unit
    return span.units[0]


def test_should_not_copy_backref_entities_or_units() -> None:
    """A back-reference span carries only entities anchored in its own text."""
    result = _backref_chain()
    _, mid, tail = result.spans
    for span in (mid, tail):
        assert span.units is not None
        assert sum(1 for u in span.units if u.unit_type == "ISNAD_UNIT") <= 1
        for entity in span.entities or []:
            assert 0 <= entity.char_start < entity.char_end <= len(span.text)
    mid_names = {e.text for e in mid.entities or []}
    assert not {"سعد بن عبد الله", "أبي"} & mid_names
    offsets = [(e.char_start, e.char_end) for e in (mid.entities or [])]
    assert len(offsets) == len(set(offsets))


def test_should_resolve_backref_pointers_to_the_literal_isnad() -> None:
    """Both back-reference spans point at the root span's literal ISNAD unit."""
    result = _backref_chain()
    root, mid, tail = result.spans
    root_isnad = _pointer_unit(root)
    assert root_isnad.unit_type == "ISNAD_UNIT"
    assert "isnad_source" not in root_isnad.metadata
    mid_unit = _pointer_unit(mid)
    assert mid_unit.metadata["isnad_source"] == "back_reference"
    assert mid_unit.metadata["refers_to_span_id"] == "A"
    assert mid_unit.metadata["resolved_span_id"] == "A"
    assert mid_unit.metadata["resolved_unit_id"] == root_isnad.unit_id
    tail_unit = _pointer_unit(tail)
    assert tail_unit.metadata["isnad_source"] == "back_reference"
    assert tail_unit.metadata["refers_to_span_id"] == "B"
    assert tail_unit.metadata["resolved_span_id"] == "A"
    assert tail_unit.metadata["resolved_unit_id"] == root_isnad.unit_id
