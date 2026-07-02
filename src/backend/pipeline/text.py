"""Footnote-entry parsing and (N)-marker handling for the ported pipeline.

The segment phase splits combined footnote blocks into entries and attaches
them to the spans whose text references them; extract strips the inline
markers out of unit body text. Every regex derives from the one
``FOOTNOTE_MARKER`` definition in backend.patterns and compiles through
``cached_compile``, never inline. The tashkeel stripper lives in
backend.patterns beside the other Arabic mark classes.
"""

from __future__ import annotations

from backend.patterns import FOOTNOTE_MARKER, CompiledPattern, cached_compile

_FOOTNOTE_SPLIT_REGEX: CompiledPattern = cached_compile(rf"(?:^|\n)\s*{FOOTNOTE_MARKER}\s*")
_FOOTNOTE_MARKER_REGEX: CompiledPattern = cached_compile(FOOTNOTE_MARKER)
_FOOTNOTE_MARKER_STRIP_REGEX: CompiledPattern = cached_compile(rf"\s*{FOOTNOTE_MARKER}\s*")
_REPEATED_SPACES_REGEX: CompiledPattern = cached_compile(r" {2,}")


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


def replace_footnote_markers(text: str, replacement: str = " ") -> str:
    """Replace each inline (N) footnote marker with replacement, then collapse spaces.

    Markers sit between tokens (a narrator name carries (2) mid-chain), so the
    default replacement is a space to keep the surrounding tokens separated; pass
    an empty string to delete markers entirely (footnote-unit text where the
    reference is noise).
    """
    cleaned = _FOOTNOTE_MARKER_STRIP_REGEX.sub(replacement, text)
    return _REPEATED_SPACES_REGEX.sub(" ", cleaned)


def strip_footnote_markers(text: str) -> str:
    """Remove inline (N) footnote markers and collapse the gaps they leave.

    Convenience over replace_footnote_markers with deletion: the markers are
    references that point at footnote entries and belong in the footnote units,
    not in the body text of an isnad/matn/other content unit.
    """
    return replace_footnote_markers(text, "").strip()


def is_footnote_marker_opening(text: str, pos: int) -> bool:
    """Return True when text[pos:] opens a (N) footnote reference like (1)."""
    return _FOOTNOTE_MARKER_REGEX.match(text, pos) is not None
