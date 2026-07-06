"""Inline heading-marker splitting for the segment phase.

Detects section headings (باب/كتاب/فصل) that appear mid-paragraph followed by an
attribution, and splits mega-paragraphs at those boundaries. Ported from
sol-next's src/utils/boundaries_headings.py.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

from backend.patterns import CompiledPattern, cached_compile, strip_tashkeel
from backend.pipeline.toc_alignment import AnchoredParagraph, TocAnchor

_SENTENCE_END_CHARS: Final[frozenset[str]] = frozenset('.؟؛!»"]})')
_ENTRY_MARKER_PREFIX: Final[str] = r"\s*\*?\s*"
_ENTRY_ATTRIBUTION_WINDOW: Final[int] = 16


def _split_paragraphs_at(
    paragraphs: list[AnchoredParagraph],
    find_positions: Callable[[str], list[int]],
) -> list[AnchoredParagraph]:
    """Split each paragraph at the char positions ``find_positions`` returns for it.

    The TOC anchor rides with the first resulting part so the paragraph's opening
    keeps the anchor it was placed on.
    """
    result: list[AnchoredParagraph] = []
    for text, pg_start, pg_end, anchor in paragraphs:
        positions = find_positions(text)
        if not positions:
            result.append((text, pg_start, pg_end, anchor))
            continue
        prev = 0
        head_anchor: TocAnchor | None = anchor
        for split_pos in positions:
            before = text[prev:split_pos].strip()
            if before:
                result.append((before, pg_start, pg_end, head_anchor))
                head_anchor = None
            prev = split_pos
        remaining = text[prev:].strip()
        if remaining:
            result.append((remaining, pg_start, pg_end, head_anchor))
    return result


def build_inline_heading_re(
    raw_patterns: list[dict[str, Any]],
    heading_marker_id: str = "HEADING_MARKER",
) -> CompiledPattern | None:
    """Build a heading regex for mid-text matching (no ^ anchor).

    Takes the HEADING_MARKER regex from config and strips the ^ anchor (and a
    leading [..]* repetition) so it can match heading keywords anywhere in text.
    Returns the compiled inline regex, or None if the pattern is absent.
    """
    for entry in raw_patterns:
        if entry["id"] == heading_marker_id:
            body = entry["regex"]
            if body.startswith("^"):
                body = body[1:]
            if body.startswith("["):
                bracket_end = body.index("]")
                if bracket_end + 1 < len(body) and body[bracket_end + 1] == "*":
                    body = body[bracket_end + 2 :]
            return cached_compile(body)
    return None


@dataclass(frozen=True, slots=True)
class HeadingCues:
    """Compiled regexes + thresholds for inline-heading splitting."""

    inline_heading_re: CompiledPattern
    attribution_strong_re: CompiledPattern
    min_heading_chars: int
    name_prefix_tokens: frozenset[str] = frozenset()
    max_heading_chars: int = 0


def split_at_inline_headings(
    paragraphs: list[AnchoredParagraph],
    cues: HeadingCues,
) -> list[AnchoredParagraph]:
    """Split paragraphs at inline heading markers followed by attribution.

    Finds heading keywords mid-paragraph, verifies ATTRIBUTION_STRONG follows (so
    the heading precedes real hadith content, not prose), and splits there.
    """
    return _split_paragraphs_at(paragraphs, lambda text: _find_inline_heading_positions(text, cues))


def _find_inline_heading_positions(text: str, cues: HeadingCues) -> list[int]:
    """Find character positions where inline heading markers start within text."""
    positions: list[int] = []
    for heading_match in cues.inline_heading_re.finditer(text):
        pos = heading_match.start()
        if pos == 0 or not text[pos - 1].isspace():
            continue
        j = pos - 1
        while j >= 0 and text[j] in " \t":
            j -= 1
        if j < 0:
            continue
        prev_non_space_char = text[j]
        before = text[:pos].rstrip()
        prev_token = before.rsplit(None, 1)[-1] if before else ""
        if cues.name_prefix_tokens and prev_token in cues.name_prefix_tokens:
            continue
        attr_found = cues.attribution_strong_re.search(text, pos=heading_match.end())
        if attr_found is None:
            continue
        heading_text = text[pos : attr_found.start()].strip()
        if len(heading_text) < cues.min_heading_chars:
            continue
        position_clean = prev_non_space_char == "\n" or prev_non_space_char in _SENTENCE_END_CHARS
        short_heading = cues.max_heading_chars > 0 and len(heading_text) <= cues.max_heading_chars
        if not (position_clean or short_heading):
            continue
        positions.append(pos)
    return positions


def build_inline_entry_re(
    raw_patterns: list[dict[str, Any]],
    entry_marker_id: str = "NUMBERED_ENTRY",
) -> CompiledPattern | None:
    """Build a numbered-entry regex for mid-text matching (no ^ anchor, no leading gap).

    Strips the ^ anchor and the leading whitespace/ornament prefix from the config
    NUMBERED_ENTRY regex so a "N -" / "(N)" marker matches anywhere in a paragraph,
    anchored at the number itself.
    """
    for entry in raw_patterns:
        if entry["id"] == entry_marker_id:
            body = entry["regex"]
            if body.startswith("^"):
                body = body[1:]
            if body.startswith(_ENTRY_MARKER_PREFIX):
                body = body[len(_ENTRY_MARKER_PREFIX) :]
            return cached_compile(body)
    return None


@dataclass(frozen=True, slots=True)
class EntryCues:
    """Compiled regexes for inline numbered-entry splitting."""

    inline_entry_re: CompiledPattern
    attribution_strong_re: CompiledPattern


def split_at_inline_entries(
    paragraphs: list[AnchoredParagraph],
    cues: EntryCues,
) -> list[AnchoredParagraph]:
    """Split paragraphs where a numbered marker runs inline into a new hadith.

    A source that prints "… بالدرة » 4 - حدثنا …" on one line merges two numbered
    hadiths into one paragraph. Split at a "N -" that follows a sentence
    terminator and is immediately followed by an attribution, so each numbered
    hadith becomes its own span.
    """
    return _split_paragraphs_at(paragraphs, lambda text: _find_inline_entry_positions(text, cues))


def _find_inline_entry_positions(text: str, cues: EntryCues) -> list[int]:
    """Positions of inline numbered markers that follow a terminator and start a hadith."""
    positions: list[int] = []
    for match in cues.inline_entry_re.finditer(text):
        pos = match.start()
        before = text[:pos].rstrip()
        if not before or before[-1] not in _SENTENCE_END_CHARS:
            continue
        window = strip_tashkeel(text[match.end() : match.end() + _ENTRY_ATTRIBUTION_WINDOW])
        if cues.attribution_strong_re.search(window) is None:
            continue
        positions.append(pos)
    return positions
