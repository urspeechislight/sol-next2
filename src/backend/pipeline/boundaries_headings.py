"""Inline heading-marker splitting for the segment phase.

Detects section headings (باب/كتاب/فصل) that appear mid-paragraph followed by an
attribution, and splits mega-paragraphs at those boundaries. Ported from
sol-next's src/utils/boundaries_headings.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.toc_alignment import AnchoredParagraph, TocAnchor

_SENTENCE_END_CHARS: Final[frozenset[str]] = frozenset('.؟؛!»"]})')


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
    """Split paragraphs containing inline heading markers followed by attribution.

    Finds heading keywords mid-paragraph, verifies ATTRIBUTION_STRONG follows (so
    the heading precedes real hadith content, not prose), and splits at the
    heading position. The TOC anchor rides with the first resulting part, which
    keeps the paragraph's opening text the anchor was placed on.
    """
    result: list[AnchoredParagraph] = []
    for text, pg_start, pg_end, anchor in paragraphs:
        positions = _find_inline_heading_positions(text, cues)
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
