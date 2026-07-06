"""Regression tests for the AN_CHAIN_INITIAL pattern precision.

A chain-initial عن opens an isnad and is always followed by a narrator name.
Prepositional عن at a span start (عن هذا الأخير = "from this latter one",
عن الذي = "about the one who") is not a chain; when it fired AN_CHAIN_INITIAL it
routed an editor's introductory prose to HADITH_TRANSMISSION, which the narrator
chain-walker then turned into non-name fragments. The pattern must fire on real
chains and stay silent on prepositional عن before a demonstrative, a relative
pronoun, or a place adverb.
"""

from __future__ import annotations

import pytest

from backend.pipeline.config import load_config

_PATTERN = dict(load_config().compiled_patterns)["AN_CHAIN_INITIAL"]


@pytest.mark.parametrize(
    "text",
    [
        "عن مالك بن أنس عن نافع",
        "عن أبي هريرة قال",
        "عن ابن عباس رضي الله عنه",
        "عن الأعمش عن إبراهيم",
        "وعن سفيان الثوري",
    ],
)
def test_should_fire_on_a_real_narrator_chain(text: str) -> None:
    assert _PATTERN.match(text) is not None


@pytest.mark.parametrize(
    "text",
    [
        'وعن هذا الأخير روى ابن سعد كتابه " جمهرة الأنساب "',
        "عن هذه الطبقات",
        "عن ذلك الأمر",
        "عن الذي ترجم له",
        "عن هؤلاء الرواة",
    ],
)
def test_should_not_fire_on_prepositional_an_before_a_non_name(text: str) -> None:
    assert _PATTERN.match(text) is None
