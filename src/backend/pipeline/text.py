"""Arabic text helpers for the ported pipeline.

Minimal segment-phase surface today: tashkeel stripping for diacritic-insensitive
TOC title matching. The footnote-entry helpers (split_footnote_entries_to_dict,
FOOTNOTE_MARKER_RE) land alongside the segment phase that consumes them. Every
regex compiles through backend.patterns.cached_compile (CENTRAL-002).
"""

from __future__ import annotations

from backend.patterns import CompiledPattern, cached_compile

_ARABIC_DIACRITICS: CompiledPattern = cached_compile(r"[ؐ-ًؚ-ٰٟۖ-ۜ۟-ۤۧ-۪ۨ-ۭ]")


def strip_tashkeel(text: str) -> str:
    """Remove Arabic diacritics (tashkeel) for diacritic-insensitive matching."""
    return _ARABIC_DIACRITICS.sub("", text)
