"""Tests for the Arabic fold SSOT in ``backend.patterns``.

``fold_search`` is the single rule the corpus index + every query are folded
by; these lock in that it is insensitive to diacritics AND letter-variant
spelling, while ``strip_diacritics`` (display) changes no letters.
"""

from __future__ import annotations

from backend.patterns import fold_search, normalize_arabic, strip_diacritics


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
