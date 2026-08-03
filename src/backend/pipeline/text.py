"""Footnote-entry parsing and (N)-marker handling for the ported pipeline.

The segment phase splits combined footnote blocks into entries and attaches
them to the spans whose text references them; extract strips the inline
markers out of unit body text; the reader serving path splits the same blocks
into the page apparatus it serves. Every regex derives from the one
``FOOTNOTE_MARKER`` definition in backend.patterns and compiles through
``cached_compile``, never inline. The tashkeel stripper lives in
backend.patterns beside the other Arabic mark classes.
"""

from __future__ import annotations

from backend.core.constants import HADITH__FOOTNOTE_MARKER_MAX_GAP
from backend.core.logging import get_logger
from backend.patterns import FOOTNOTE_MARKER, CompiledPattern, cached_compile

_logger = get_logger("shia-library.pipeline.text")

_FOOTNOTE_SPLIT_REGEX: CompiledPattern = cached_compile(rf"(?:^|\n)\s*{FOOTNOTE_MARKER}[ \t]*")
"""Entry-head split: a line-start ``(N)`` followed by horizontal space only.
A greedy trailing ``\\s*`` would swallow the newline before a consecutive
head, merging a dangling empty entry like ``(1)`` with the next entry's
text; keeping the trailing class horizontal preserves every head."""

_FOOTNOTE_MARKER_REGEX: CompiledPattern = cached_compile(FOOTNOTE_MARKER)
_FOOTNOTE_MARKER_STRIP_REGEX: CompiledPattern = cached_compile(rf"\s*{FOOTNOTE_MARKER}\s*")
_REPEATED_SPACES_REGEX: CompiledPattern = cached_compile(r" {2,}")


def split_footnote_block(footnote_text: str, *, context: str = "") -> list[tuple[str | None, str]]:
    """Split a footnote block into ordered (marker, text) entries, losslessly.

    The block is shaped ``(1) first\\n(2) second``, optionally led by text
    before the first ``(N)`` head. That lead text is a real part of the
    apparatus (an unnumbered editorial note, or the continuation of the
    previous page's entry in continuously numbered editions, ~17% of corpus
    fields) and is preserved as a leading ``(None, text)`` entry. A block with
    no ``(N)`` heads at all yields a single ``(None, block)`` entry. Every
    non-empty piece of the block lands in exactly one entry, so a ``None``
    marker always means "the edition printed no number here", never a parse
    failure.

    A split head whose number is not a plausible continuation of the block's
    own sequence — not strictly increasing, or increasing by more than
    ``HADITH__FOOTNOTE_MARKER_MAX_GAP`` — is not treated as a new entry: it is
    a reference number that happened to open a line (the sequential-
    plausibility guard from docs/councils/2026-07-03-reader-footnotes-
    council.md). It is logged and folded back into the preceding entry's
    text, so a rejected number is still preserved verbatim rather than
    invented as, or silently discarded as, a bogus marker. ``context`` (a
    book/page or span identifier) tags the log line.
    """
    parts = _FOOTNOTE_SPLIT_REGEX.split(footnote_text)
    entries: list[tuple[str | None, str]] = []
    preamble = parts[0].strip()
    if preamble:
        entries.append((None, preamble))
    last_accepted: int | None = None
    for index in range(1, len(parts) - 1, 2):
        text = parts[index + 1].strip()
        if not text:
            continue
        marker = parts[index]
        marker_value = int(marker)
        if last_accepted is not None and not (
            last_accepted < marker_value <= last_accepted + HADITH__FOOTNOTE_MARKER_MAX_GAP
        ):
            _logger.warning(
                "footnote-marker-implausible",
                context=context,
                marker=marker,
                previous=last_accepted,
            )
            prev_marker, prev_text = entries[-1]
            entries[-1] = (prev_marker, f"{prev_text} ({marker}) {text}")
            continue
        entries.append((marker, text))
        last_accepted = marker_value
    return entries


def split_footnote_entries(footnote_text: str, *, context: str = "") -> list[tuple[str, str]]:
    """Split a combined footnote block into numbered (number, text) entries.

    The numbered projection of :func:`split_footnote_block`: pipeline callers
    attach entries to spans by number, so unnumbered lead text has no
    attachment target and is projected out here.
    """
    return [
        (marker, text)
        for marker, text in split_footnote_block(footnote_text, context=context)
        if marker is not None
    ]


def split_footnote_entries_to_dict(footnote_text: str, *, context: str = "") -> dict[str, str]:
    """Split a footnote block into a number -> text mapping for dict callers."""
    return dict(split_footnote_entries(footnote_text, context=context))


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
