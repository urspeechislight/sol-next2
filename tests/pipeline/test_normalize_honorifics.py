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
