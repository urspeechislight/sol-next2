"""Tests for person-name refinement: leading-token strip + non-name rejection.

Locks the precision fixes that stop the person extractors emitting divine names,
title fragments, kinship references, and verb-led fragments, while preserving
real names including theophoric compounds and imam laqabs.
"""

from __future__ import annotations

import pytest

from backend.pipeline.config import load_config
from backend.pipeline.name_extraction import refine_person_name

_CFG = load_config().raw["narrator_extraction"]
_REJECT = frozenset(_CFG["person_reject_words"])
_STRIP = frozenset(_CFG["leading_strip_words"])
_KINSHIP = frozenset(_CFG["kinship_words"])


def _refine(name: str) -> str | None:
    return refine_person_name(name, _REJECT, _STRIP, _KINSHIP)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("قال ابن شهاب", "ابن شهاب"),
        ("فقال ابن عباس", "ابن عباس"),
        ("كان ابن عمر", "ابن عمر"),
        ("يا ابن جريج", "ابن جريج"),
    ],
)
def test_should_strip_a_leading_verb_or_vocative(raw: str, expected: str) -> None:
    assert _refine(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "الله",
        "المؤمنين",
        "أم المؤمنين",
        "أمير المؤمنين",
        "يا ابن أخي",
        "ابن أخي",
        "عمه",
        "رسول الله",
        "النبي",
        "الله بن آدم",
        "رسول الله بن خطل",
    ],
)
def test_should_reject_a_non_name(raw: str) -> None:
    assert _refine(raw) is None


@pytest.mark.parametrize(
    "raw",
    ["عبد الله بن يوسف", "عبد الله", "عبد الرحمن بن عوف", "الصادق", "أبو هريرة", "محمد بن إسماعيل"],
)
def test_should_preserve_a_real_name(raw: str) -> None:
    assert _refine(raw) == raw


@pytest.mark.parametrize("raw", ["عَمِّهِ", "اللَّهِ", "أَخِيهِ"])
def test_should_reject_a_vowelled_non_name(raw: str) -> None:
    """Refinement compares tashkeel-stripped tokens, so vowelled forms reject too."""
    assert _refine(raw) is None


def test_should_strip_a_vowelled_leading_verb() -> None:
    """A vowelled leading verb (كَانَ) is stripped like its unvowelled form."""
    assert _refine("كَانَ ابن عمر") == "ابن عمر"
