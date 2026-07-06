"""Tests for inline numbered-entry splitting.

A source that prints two numbered hadiths on one line ("… » 4 - حدثنا …") should
be split into one paragraph per entry, but only where the marker follows a
sentence terminator and is immediately followed by an attribution — a bare year
number mid-sentence must not split.
"""

from __future__ import annotations

from backend.patterns import cached_compile
from backend.pipeline.boundaries_headings import (
    EntryCues,
    build_inline_entry_re,
    split_at_inline_entries,
)
from backend.pipeline.config import load_config

_CFG = load_config()
_ENTRY_RE = build_inline_entry_re(_CFG.raw["patterns"])
_ATTR = next(p["regex"] for p in _CFG.raw["patterns"] if p["id"] == "ATTRIBUTION_STRONG")
assert _ENTRY_RE is not None
_CUES = EntryCues(_ENTRY_RE, cached_compile(_ATTR))


def _split(text: str) -> list[str]:
    parts = split_at_inline_entries([(text, 1, 1, None)], _CUES)
    return [p[0] for p in parts]


def test_should_split_two_hadiths_run_together_inline() -> None:
    """An inline '4 -' after a hadith's closing » starts a new entry."""
    text = "3 - حدثنا محمد عن أبي هريرة قال كذا » 4 - حدثنا محمد عن جابر أن النبي قال كذا »"
    parts = _split(text)
    assert len(parts) == 2
    assert parts[0].startswith("3 -")
    assert parts[1].startswith("4 -")


def test_should_not_split_a_year_number_mid_sentence() -> None:
    """A number that is not followed by an attribution is left in place."""
    text = "توفي في سنة 5 من الهجرة وكان من أصحاب النبي"
    assert _split(text) == [text]


def test_should_not_split_a_marker_without_a_preceding_terminator() -> None:
    """A numbered marker not preceded by a sentence terminator does not split."""
    text = "الحديث رقم 4 - حدثنا فلان"
    assert _split(text) == [text]
