"""Arabic text helpers for the ported pipeline.

Minimal segment-phase surface: tashkeel stripping for diacritic-insensitive TOC
title matching, plus the footnote-entry parsing and (N)-marker attachment the
segment phase consumes. Every regex compiles through the central
backend.patterns.cached_compile helper, never inline.
"""

from __future__ import annotations

from backend.patterns import CompiledPattern, cached_compile

_ARABIC_DIACRITICS: CompiledPattern = cached_compile(r"[ؐ-ًؚ-ٰٟۖ-ۜ۟-ۤۧ-۪ۨ-ۭ]")


def strip_tashkeel(text: str) -> str:
    """Remove Arabic diacritics (tashkeel) for diacritic-insensitive matching."""
    return _ARABIC_DIACRITICS.sub("", text)


_FOOTNOTE_SPLIT_REGEX: CompiledPattern = cached_compile(r"(?:^|\n)\s*\((\d+)\)\s*")
_FOOTNOTE_MARKER_REGEX: CompiledPattern = cached_compile(r"\((\d+)\)")


def split_footnote_entries(footnote_text: str) -> list[tuple[str, str]]:
    """Split a combined footnote block into (number, text) entries.

    The block is shaped ``(1) first\\n(2) second``. The split regex yields
    [preamble, num, text, num, text, ...]; entries with empty text are skipped.
    """
    parts = _FOOTNOTE_SPLIT_REGEX.split(footnote_text)
    entries: list[tuple[str, str]] = []
    for index in range(1, len(parts) - 1, 2):
        number = parts[index]
        text = parts[index + 1].strip()
        if text:
            entries.append((number, text))
    return entries


def split_footnote_entries_to_dict(footnote_text: str) -> dict[str, str]:
    """Split a footnote block into a number -> text mapping for dict callers."""
    return dict(split_footnote_entries(footnote_text))


def attach_footnote_text(span_text: str, footnote_entries: dict[str, str]) -> str | None:
    """Return the footnote entries whose (N) markers appear in span_text.

    Markers are matched in span order, deduplicated, and joined as ``(N) text``
    lines. Returns None when there are no entries or no marker matches — the span
    then has no footnote block to attach.
    """
    if not footnote_entries:
        return None
    matched: list[str] = []
    seen: set[str] = set()
    for marker in _FOOTNOTE_MARKER_REGEX.findall(span_text):
        if marker in footnote_entries and marker not in seen:
            matched.append(f"({marker}) {footnote_entries[marker]}")
            seen.add(marker)
    return "\n".join(matched) if matched else None
