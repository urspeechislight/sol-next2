"""Tests for the Arabic fold SSOT in ``backend.patterns``.

``fold_search`` is the single rule the corpus index + every query are folded
by; these lock in that it is insensitive to diacritics AND letter-variant
spelling, while ``strip_diacritics`` (display) changes no letters.
``fold_with_offsets`` is the one folded→original index map both the corpus
snippet locator and the gazetteer scan build on.
"""

from __future__ import annotations

from backend.patterns import (
    fold_search,
    fold_with_offsets,
    normalize_arabic,
    strip_diacritics,
)


def test_should_fold_alef_hamza_when_searching() -> None:
    """A hamza-seated alef folds to bare alef, so the spellings match."""
    assert fold_search("أَوْلِيَاءَ") == fold_search("اولياء")
    assert fold_search("إنسان") == fold_search("انسان")


def test_should_fold_alef_maqsura_and_taa_marbuta_when_searching() -> None:
    """alef-maqsura folds to yaa and taa-marbuta to haa."""
    assert fold_search("عَلَى") == fold_search("علي")
    assert fold_search("مكتبة") == fold_search("مكتبه")


def test_should_strip_annotation_signs_when_searching() -> None:
    """Quranic waqf/sajdah signs are dropped, not turned into tokens."""
    folded = fold_search("جَهَنَّمُ ۖ وَلَا")
    assert "ۖ" not in folded
    assert folded.split() == ["جهنم", "ولا"]


def test_should_keep_letters_when_stripping_diacritics_for_display() -> None:
    """The display strip removes vowel marks but folds no letters."""
    assert strip_diacritics("أَوْلِيَاءُ") == "أولياء"
    assert "أ" in strip_diacritics("أَوْلِيَاءُ")


def test_should_collapse_whitespace_when_normalizing_a_name() -> None:
    """The name fold folds letters and collapses runs of whitespace."""
    assert normalize_arabic("عَلِيّ   بنُ  أبي") == "علي بن ابي"


def test_should_map_each_folded_char_to_its_source_index() -> None:
    """Plain text folds 1:1, so offsets are the identity plus a length sentinel."""
    folded, offsets = fold_with_offsets("علي")
    assert folded == "علي"
    assert offsets == [0, 1, 2, 3]


def test_should_skip_dropped_marks_in_the_offset_map() -> None:
    """The fatha at source index 1 folds to nothing, so no folded char points at
    that index and the next letter's offset jumps past it."""
    folded, offsets = fold_with_offsets("عَلي")
    assert folded == "علي"
    assert offsets == [0, 2, 3, 4]


def test_should_map_a_folded_span_back_over_trailing_marks() -> None:
    """A folded span ``[fs, fe)`` maps to ``[offsets[fs], offsets[fe])``; with a
    kasratan on the final letter, the mapped window keeps that trailing mark."""
    text = "بدرٍ"
    folded, offsets = fold_with_offsets(text)
    assert folded == "بدر"
    assert text[offsets[0] : offsets[3]] == "بدرٍ"


def test_should_expose_the_trailing_sentinel_for_a_full_length_span() -> None:
    """One offset per folded char plus a sentinel of ``len(text)``, so a span ending
    at ``len(folded)`` resolves."""
    text = "خيبر"
    folded, offsets = fold_with_offsets(text)
    assert len(offsets) == len(folded) + 1
    assert offsets[-1] == len(text)
