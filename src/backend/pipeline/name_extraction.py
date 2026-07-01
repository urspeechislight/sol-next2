"""Canonical person-name cleanup pipeline.

extract_person_name trims and cleans a text slice into a person-name candidate,
applying a fixed sequence: boundary-regex crop, end-position crop, compound-prefix
backward extension, dangling-connector strip, leading-clitic strip, and
clean_name_text. Each step is also exposed as a helper for callers that need a
custom composition.

Ported from sol-next's src/utils/name_extraction.py. The pattern-anchor input
contract: end_positions is an iterable of absolute character offsets that
hard-cut the name (callers derive them from span.patterns, e.g. LAQAB_MARKER /
DEATH_MARKER positions); this module knows nothing about Pattern or Span, by
design. The clitic-strip word-length threshold is not hard-coded here — callers
supply it from config (biography_clitic_strip_min_word_chars).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from backend.patterns import CompiledPattern
from backend.pipeline.names import (
    NARRATOR__CLITIC_CHARS,
    NARRATOR__COMPOUND_NAME_PREFIXES,
    NARRATOR__HAMZA_ALEF_CHARS,
    NARRATOR__PATRONYMIC_CONNECTORS,
    clean_name_text,
)
from backend.pipeline.text import is_footnote_marker_opening

_WORD_BREAK_CHARS: frozenset[str] = frozenset(" \t\n،,.:;()")
_CLITIC_STRIP_RAW_FLOOR: int = 2


@dataclass(frozen=True, slots=True)
class NameOptions:
    """Cropping and cleaning options for extract_person_name.

    clitic_min_word_chars is required and sourced from config — it is the minimum
    first-word length at which a leading و/ف/ل/ك/ب/س is parsed as a proclitic
    rather than a name radical, and that threshold belongs in config, not here.
    """

    boundary_regex: CompiledPattern
    clitic_min_word_chars: int
    end_positions: Iterable[int] = ()
    extend_compound_prefix: bool = True
    strip_clitic: bool = True
    strip_dangling_connector: bool = True


def extract_person_name(
    text: str,
    start: int,
    end: int,
    opts: NameOptions,
) -> tuple[str, int, int] | None:
    """Trim and clean text[start:end] into a person-name candidate.

    Applies, in order: boundary-regex crop, end-position crop, compound-prefix
    backward extension, dangling-connector strip, leading-clitic strip, and
    clean_name_text. Returns (cleaned_text, abs_start, abs_end) referring to the
    absolute view of text and reflecting any backward extension or forward strip,
    or None when the cleaned text is empty.
    """
    cropped_end = _crop_at_boundary(text, start, end, opts.boundary_regex)
    cropped_end = _crop_at_end_positions(start, cropped_end, opts.end_positions)
    name_start = start
    if opts.extend_compound_prefix:
        name_start = _extend_compound_prefix_back(text, name_start)
    raw = text[name_start:cropped_end].rstrip()
    if opts.strip_dangling_connector:
        raw = strip_dangling_tail(raw)
    lead_offset = 0
    if opts.strip_clitic:
        raw, lead_offset = strip_leading_clitic(raw, opts.clitic_min_word_chars)
    cleaned = clean_name_text(raw)
    if not cleaned:
        return None
    return (cleaned, name_start + lead_offset, name_start + lead_offset + len(raw))


def _crop_at_boundary(text: str, start: int, end: int, boundary_regex: CompiledPattern) -> int:
    """Return end cropped at the first boundary_regex hit in text[start:end].

    A '(' that opens a footnote marker like (1) is skipped so a footnote reference
    does not truncate the name spuriously.
    """
    text_slice = text[start:end]
    for boundary_match in boundary_regex.finditer(text_slice):
        opens_footnote = boundary_match.group() == "(" and is_footnote_marker_opening(
            text_slice, boundary_match.start()
        )
        if opens_footnote:
            continue
        return start + boundary_match.start()
    return end


def _crop_at_end_positions(start: int, end: int, end_positions: Iterable[int]) -> int:
    """Return end cropped at the smallest position strictly within (start, end)."""
    for position in end_positions:
        if start < position < end:
            end = position
    return end


def _extend_compound_prefix_back(text: str, start: int) -> int:
    """Walk one token backward; include it when it is a compound-name prefix.

    Theophoric/kunya names lex as two tokens (عبد X, أبو X, أمّ X); a patronymic
    regex starting at the second token misses the first. This covers the bare form
    and the clitic-prefixed form (وعبد, فعبد) by stripping a leading proclitic
    before the membership check.
    """
    cursor = start
    while cursor > 0 and text[cursor - 1] in " \t":
        cursor -= 1
    if cursor in (0, start):
        return start
    prev_end = cursor
    while cursor > 0 and text[cursor - 1] not in _WORD_BREAK_CHARS:
        cursor -= 1
    prev_word = text[cursor:prev_end]
    if prev_word in NARRATOR__COMPOUND_NAME_PREFIXES:
        return cursor
    is_clitic_compound = (
        prev_word[0] in NARRATOR__CLITIC_CHARS and prev_word[1:] in NARRATOR__COMPOUND_NAME_PREFIXES
    )
    if is_clitic_compound:
        return cursor + 1
    return start


def strip_dangling_tail(raw: str) -> str:
    """Drop trailing bare بن/ابن tokens left by a truncated patronymic chain.

    Belt-and-suspenders: the patronymic regex should not emit these, but its
    optional second-word slot can capture a stray بن before the next iteration
    fails to match, leaving the chain hanging.
    """
    parts = raw.rstrip().split()
    while parts and parts[-1] in NARRATOR__PATRONYMIC_CONNECTORS:
        parts.pop()
    return " ".join(parts)


def strip_leading_clitic(raw: str, min_word_chars: int) -> tuple[str, int]:
    """Strip a 1-char proclitic on the first word.

    Two triggers: the next character is a hamza-alef (أ/إ/آ/ا/ء) — unambiguous,
    strip; or the first word has at least min_word_chars characters — long Arabic
    words rarely begin with و/ف/ل/ك/ب/س as a first radical. A candidate of two
    characters or fewer has no room for a clitic plus a stem and is left alone.
    Returns (cleaned, lead_offset) so callers can advance the absolute start.
    """
    if len(raw) <= _CLITIC_STRIP_RAW_FLOOR:
        return (raw, 0)
    first_word = raw.split(maxsplit=1)[0]
    if first_word[0] not in NARRATOR__CLITIC_CHARS:
        return (raw, 0)
    if first_word[1:2] in NARRATOR__HAMZA_ALEF_CHARS:
        return (raw[1:], 1)
    if len(first_word) >= min_word_chars:
        return (raw[1:], 1)
    return (raw, 0)
