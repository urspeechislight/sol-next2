"""Detection must be tashkeel-insensitive with offsets mapped to the original text.

A fully vowelled manuscript (عَنْ / حَدَّثَنَا) has to match the same unvowelled
transmission patterns as a plain one, or its whole isnad collapses into a single
narrator. The Pattern offsets must still point into the original vowelled text.
"""

from __future__ import annotations

from backend.pipeline.config import load_config
from backend.pipeline.segment import _detection_view, detect_patterns

_PATTERNS = dict(load_config().compiled_patterns)


def test_should_map_stripped_offsets_to_the_original() -> None:
    """عَنْ strips to عن; the index map points each surviving char at the original."""
    view, index_map = _detection_view("عَنْ")
    assert view == "عن"
    assert index_map == [0, 2, 4]


def test_should_detect_attribution_when_the_isnad_is_vowelled() -> None:
    """The vowelled عَنْ is detected and its matched slice is the original vowelled text."""
    text = "حَدَّثَنَا زَيْدٌ عَنْ عَمْرٍو"
    detected = detect_patterns(text, _PATTERNS)
    an = [p for p in detected if p.pattern_id in {"ATTRIBUTION", "AN_CHAIN_INITIAL"}]
    assert an, "no attribution detected in vowelled isnad"
    for pattern in detected:
        assert text[pattern.char_start : pattern.char_end] == pattern.matched_text


def test_should_detect_attribution_when_the_text_is_unvowelled() -> None:
    """Stripping is a no-op on unvowelled text: patterns still fire unchanged."""
    text = "حدثنا زيد عن عمرو"
    detected = detect_patterns(text, _PATTERNS)
    assert any(p.pattern_id == "ATTRIBUTION" for p in detected)
