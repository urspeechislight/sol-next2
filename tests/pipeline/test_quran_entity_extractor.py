"""Tests for the Qurʾān named-entity extractor.

Fixtures are real Qurʾānic phrases. The extractor must anchor each entity to its
exact pointed-text window, categorize it, strip a leading conjunction/preposition
clitic from the entity while still matching it, keep an ambiguous name only where
its validated preceding-word rule allows (صالح after أخاهم but not after عمل; عاد
in إلى عاد but not in فمن عاد), and stay silent outside the Qurʾān genre.
"""

from __future__ import annotations

from typing import Any

from backend.pipeline.config import load_config
from backend.pipeline.extractors.quran_entities import quran_entity_extractor
from backend.pipeline.models import HierarchyPath, Span

_CFG = load_config()
_QURAN_GENRE = "quran"


def _span(text: str, book_type: str | None) -> Span:
    metadata: dict[str, Any] = {}
    if book_type is not None:
        metadata["book_type"] = book_type
    return Span(
        span_id="s_quran",
        text=text,
        page_start=1,
        page_end=1,
        span_type="VERSE",
        behavior="QURAN_VERSE",
        hierarchy=HierarchyPath(path=["سورة"], path_ids=["s1"], depth=1),
        metadata=metadata,
    )


def _named(text: str) -> dict[str, str]:
    entities = quran_entity_extractor(_span(text, _QURAN_GENRE), _CFG)
    return {e.metadata["name"]: e.metadata["category"] for e in entities}


def test_should_extract_unambiguous_named_entities() -> None:
    """A plain prophet/person name is named with its category."""
    assert _named("وَهَلْ أَتَاكَ حَدِيثُ مُوسَىٰ") == {"موسى": "prophet"}
    assert _named("إِنَّ فِرْعَوْنَ عَلَا فِي الْأَرْضِ") == {"فرعون": "person"}


def test_should_strip_a_leading_clitic_from_the_entity() -> None:
    """A conjunction/preposition clitic is matched but excluded from the entity window."""
    span = _span("قَوْمَ نُوحٍ وَعَادٍ وَثَمُودَ", _QURAN_GENRE)
    entities = quran_entity_extractor(span, _CFG)
    by_name = {e.metadata["name"]: e for e in entities}
    assert set(by_name) == {"نوح", "عاد", "ثمود"}
    assert by_name["عاد"].text == "عَادٍ"
    assert span.text[by_name["عاد"].char_start : by_name["عاد"].char_end] == "عَادٍ"


def test_should_keep_an_ambiguous_name_only_in_its_entity_frame() -> None:
    """صالح is the prophet after أخاهم, but the adjective in عملاً صالحاً is dropped."""
    assert _named("وَإِلَىٰ ثَمُودَ أَخَاهُمْ صَالِحًا") == {"ثمود": "people", "صالح": "prophet"}
    assert quran_entity_extractor(_span("وَمَنْ آمَنَ وَعَمِلَ صَالِحًا", _QURAN_GENRE), _CFG) == []


def test_should_drop_the_common_word_reading_by_preceding_word() -> None:
    """عاد is the people after إلى, but the verb in فمن عاد is dropped."""
    assert _named("وَإِلَىٰ عَادٍ أَخَاهُمْ هُودًا") == {"عاد": "people", "هود": "prophet"}
    assert quran_entity_extractor(_span("فَمَنْ عَادَ فَيَنْتَقِمُ اللَّهُ مِنْهُ", _QURAN_GENRE), _CFG) == []


def test_should_match_the_accusative_alif_form() -> None:
    """A triptote name in the accusative (نوحًا) matches and groups under its base name."""
    entities = quran_entity_extractor(_span("وَلَقَدْ أَرْسَلْنَا نُوحًا إِلَىٰ قَوْمِهِ", _QURAN_GENRE), _CFG)
    assert [(e.text, e.metadata["name"]) for e in entities] == [("نُوحًا", "نوح")]


def test_should_anchor_each_entity_to_exact_offsets() -> None:
    """Every entity's char window reproduces its pointed-text surface exactly."""
    verse = "وَإِلَىٰ ثَمُودَ أَخَاهُمْ صَالِحًا قَالَ يَا قَوْمِ"
    entities = quran_entity_extractor(_span(verse, _QURAN_GENRE), _CFG)
    assert entities
    for entity in entities:
        assert verse[entity.char_start : entity.char_end] == entity.text


def test_should_extract_nothing_outside_quran_genre() -> None:
    """A verse quoted inside a hadith or untyped book yields no Qurʾān entities."""
    assert quran_entity_extractor(_span("وَهَلْ أَتَاكَ حَدِيثُ مُوسَىٰ", "shia-hadith-general"), _CFG) == []
    assert quran_entity_extractor(_span("وَهَلْ أَتَاكَ حَدِيثُ مُوسَىٰ", None), _CFG) == []
