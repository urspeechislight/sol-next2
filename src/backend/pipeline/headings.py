"""HEADING_MARKER post-detection filters for the segment phase.

The HEADING_MARKER regex is intentionally permissive — it accepts كتاب|باب|فصل
with optional ال prefix and a trailing-whitespace lookahead. That is too generous
for long sīrah/tarīkh prose where heading keywords also appear as common nouns
(مطلب = "demand") or as the tail half of a proper name split across pages
(عبد المطلب). Two layered filters narrow the false-positive surface:

  * disqualifiers — trailing-context shapes that look like narrative continuations
    (possessive pronouns, conjunction+verb, ...). If any matches, HEADING_MARKER
    is removed.
  * qualifiers — trailing-context shapes that look like a heading (ordinal word,
    digit, "في" topic frame, decorative wrapper, end-of-line, ال + noun). If none
    matches and the keyword's own match span has no numeric/decorative prefix,
    HEADING_MARKER is removed.

Both lists live in config under the HEADING_MARKER pattern entry. Ported from
sol-next's src/utils/headings.py.
"""

from __future__ import annotations

import re
from typing import Any

from backend.core.constants import HADITH__PATTERN_HEADING_MARKER as HEADING_MARKER_ID
from backend.core.errors import SegmentError
from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.models import Pattern

_HEADING_PREFIX_CHARS_RE: CompiledPattern = cached_compile(r"[0-9٠-٩*()]")

_NARRATIVE_EVIDENCE_PATTERN_IDS: frozenset[str] = frozenset(
    {
        "CLASSICAL_SOURCE_ATTRIBUTION",
        "HIJRI_YEAR",
        "LUNAR_MONTH",
        "DEATH_MARKER",
        "BIRTH_MARKER",
    }
)

_CHEAP_PATTERNS_DROPPED_BY_NARRATIVE: frozenset[str] = frozenset({HEADING_MARKER_ID, "FIQH_RULING"})


def _find_heading_entry(raw_patterns: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the HEADING_MARKER pattern entry from config, or None if absent."""
    for entry in raw_patterns:
        if entry["id"] == HEADING_MARKER_ID:
            return entry
    return None


def parse_heading_disqualifiers(raw_patterns: list[dict[str, Any]]) -> list[CompiledPattern]:
    """Compile heading disqualifier regexes from the HEADING_MARKER config.

    Disqualifiers are checked against the text immediately following the heading
    keyword match; when any matches, HEADING_MARKER is being used in its
    common-noun sense and must not count for behavior routing.
    """
    entry = _find_heading_entry(raw_patterns)
    if entry is None or "heading_disqualifiers" not in entry:
        return []
    compiled: list[CompiledPattern] = []
    for dq_regex in entry["heading_disqualifiers"]:
        try:
            compiled.append(cached_compile(dq_regex))
        except re.error as exc:
            raise SegmentError(f"Invalid disqualifier regex {dq_regex!r}: {exc}") from exc
    return compiled


def parse_heading_qualifiers(raw_patterns: list[dict[str, Any]]) -> list[CompiledPattern]:
    """Compile heading qualifier regexes from the HEADING_MARKER config.

    Qualifiers express positive trailing-context shapes that confirm a keyword is
    structural (ordinal, digit, في-frame, ...). Raises SegmentError on a missing
    after_match key or an invalid regex.
    """
    entry = _find_heading_entry(raw_patterns)
    if entry is None or "heading_qualifiers" not in entry:
        return []
    compiled: list[CompiledPattern] = []
    for q_entry in entry["heading_qualifiers"]:
        regex = q_entry.get("after_match") if isinstance(q_entry, dict) else None
        if not regex:
            raise SegmentError(f"Qualifier missing after_match: {q_entry!r}") from None
        try:
            compiled.append(cached_compile(regex))
        except re.error as exc:
            raise SegmentError(f"Invalid qualifier regex {regex!r}: {exc}") from exc
    return compiled


def filter_heading_disqualifiers(
    text: str,
    detected_patterns: list[Pattern],
    disqualifiers: list[CompiledPattern],
) -> list[Pattern]:
    """Remove HEADING_MARKER patterns when post-keyword text matches a disqualifier."""
    if not disqualifiers:
        return detected_patterns
    heading_matches = [p for p in detected_patterns if p.pattern_id == HEADING_MARKER_ID]
    if not heading_matches:
        return detected_patterns
    earliest = min(heading_matches, key=lambda p: p.char_start)
    after_text = text[earliest.char_end :]
    for dq in disqualifiers:
        if dq.match(after_text):
            return [p for p in detected_patterns if p.pattern_id != HEADING_MARKER_ID]
    return detected_patterns


def filter_heading_shape(
    text: str,
    detected_patterns: list[Pattern],
    qualifiers: list[CompiledPattern],
) -> list[Pattern]:
    """Remove HEADING_MARKER patterns whose surface shape is not heading-like.

    A heading keyword counts as a real heading when its own match span contains a
    numeric/decorative prefix, or the text after it matches at least one
    qualifier. Otherwise the keyword is more likely a noun in running prose and
    HEADING_MARKER is removed.
    """
    if not qualifiers:
        return detected_patterns
    heading_matches = [p for p in detected_patterns if p.pattern_id == HEADING_MARKER_ID]
    if not heading_matches:
        return detected_patterns
    earliest = min(heading_matches, key=lambda p: p.char_start)
    match_text = text[earliest.char_start : earliest.char_end]
    if _HEADING_PREFIX_CHARS_RE.search(match_text):
        return detected_patterns
    after_text = text[earliest.char_end :]
    for q in qualifiers:
        if q.match(after_text):
            return detected_patterns
    return [p for p in detected_patterns if p.pattern_id != HEADING_MARKER_ID]


def drop_heading_for_narrative(
    text: str,
    detected_patterns: list[Pattern],
    max_heading_length: int,
    narrative_genres: frozenset[str] = frozenset(),
    book_type: str | None = None,
) -> list[Pattern]:
    """Drop HEADING_MARKER / FIQH_RULING on a long narrative-genre span.

    A real section heading is short and structural; a real fiqh ruling is a legal
    obligation. In a narrative-genre book (sīrah, tarīkh, biography), a long
    paragraph that carries a heading/ruling keyword AND narrative-evidence
    patterns (classical-source attribution, hijri year, lunar month, death/birth
    marker) is using the keyword in running prose. Three gates must all hold:
    book_type is in the narrative-genre whitelist; span length exceeds
    max_heading_length; the span carries at least one narrative-evidence pattern.
    """
    if max_heading_length <= 0:
        return detected_patterns
    if not narrative_genres or book_type not in narrative_genres:
        return detected_patterns
    candidates = [
        p for p in detected_patterns if p.pattern_id in _CHEAP_PATTERNS_DROPPED_BY_NARRATIVE
    ]
    if not candidates:
        return detected_patterns
    if len(text) <= max_heading_length:
        return detected_patterns
    pattern_ids = {p.pattern_id for p in detected_patterns}
    if not pattern_ids.intersection(_NARRATIVE_EVIDENCE_PATTERN_IDS):
        return detected_patterns
    return [
        p for p in detected_patterns if p.pattern_id not in _CHEAP_PATTERNS_DROPPED_BY_NARRATIVE
    ]
