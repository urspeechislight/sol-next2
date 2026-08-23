"""Tests for honorific-phrase -> ligature normalization.

Standardizing spelled-out honorifics to their ligature signs is what lets the
name cleaner cut a salutation off a narrator's name uniformly, so a name no
longer absorbs رضي الله عنها or صلى الله عليه وسلم.
"""

from __future__ import annotations

import pytest

from backend.patterns import normalize_honorifics


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("عائشة رضي الله تعالى عنها", "عائشة ﵂"),
        ("قال رسول الله صلى الله عليه وسلم", "قال رسول الله ﷺ"),
        ("عن علي عليه السلام", "عن علي ﵇"),
        ("رضي الله عنهما جميعا", "﵄ جميعا"),
        ("صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ", "ﷺ"),
        ("جعفر بن محمد رحمه الله", "جعفر بن محمد ﵀"),
    ],
)
def test_should_normalize_a_spelled_out_honorific_to_its_ligature(raw: str, expected: str) -> None:
    assert normalize_honorifics(raw) == expected


@pytest.mark.parametrize("raw", ["محمد بن عبد الله", "عبد الرحمن بن عوف", "عليه دين كثير"])
def test_should_leave_a_plain_name_or_non_honorific_unchanged(raw: str) -> None:
    assert normalize_honorifics(raw) == raw


@pytest.mark.parametrize(
    ("raw", "expected_cp"),
    [
        ("عليه السلام", 0xFD47),
        ("صلى الله عليه وآله وسلم", 0xFD4C),
        ("عز وجل", 0xFDFF),
        ("رحمه الله", 0xFD40),
        ("قدس سره", 0xFD4B),
        ("سبحانه وتعالى", 0xFDFE),
    ],
)
def test_should_map_each_canon_phrase_to_its_ligature_cp(raw: str, expected_cp: int) -> None:
    assert normalize_honorifics(raw) == chr(expected_cp)


def test_should_still_normalize_a_fully_vowelled_azz_wa_jall() -> None:
    assert normalize_honorifics("عَزَّ وَجَلَّ") == chr(0xFDFF)


@pytest.mark.parametrize("raw", ["عزل وجل", "عزو وجل", "تعزل", "قال عزل وجل في غيره"])
def test_should_not_match_an_ordinary_word_that_merely_shares_the_letters(raw: str) -> None:
    assert normalize_honorifics(raw) == raw
