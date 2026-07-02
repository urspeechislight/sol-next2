"""Canonical person-name cleanup pipeline.

extract_person_name trims and cleans a text slice into a person-name
candidate: a boundary-regex crop (skipping footnote-marker parens) followed by
clean_name_text (footnote-marker replacement + trailing-punctuation strip).
Ported from sol-next's src/utils/name_extraction.py and names.py, cut down to
the path the hadith narrator extractor exercises; the compound-prefix
extension, dangling-connector strip, leading-clitic strip, end-position crop,
and the kunya/laqab/sentence-start helpers return with the biography and
rijal extractors that consume them. This module knows nothing about Pattern
or Span, by design. Every regex compiles through the central backend.patterns
module.
"""

from __future__ import annotations

from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.text import is_footnote_marker_opening, replace_footnote_markers

_NAME_TRAILING_PUNCT_REGEX: CompiledPattern = cached_compile(r"[\s،,:.]+$")


def clean_name_text(name: str) -> str:
    """Remove footnote markers (replaced with spaces) and trailing punctuation.

    Inline footnote references like (2) sit between name tokens; replacing them
    with a space keeps the tokens separated, then the trailing Arabic/Latin
    delimiters (، , : .) that are structural rather than part of the name are
    stripped.
    """
    cleaned = replace_footnote_markers(name)
    cleaned = _NAME_TRAILING_PUNCT_REGEX.sub("", cleaned)
    return cleaned.strip()


def extract_person_name(
    text: str,
    start: int,
    end: int,
    boundary_regex: CompiledPattern,
) -> tuple[str, int, int] | None:
    """Trim and clean text[start:end] into a person-name candidate.

    Crops at the first boundary_regex hit, then applies clean_name_text.
    Returns (cleaned_text, abs_start, abs_end) referring to the absolute view
    of text, or None when the cleaned text is empty.
    """
    cropped_end = _crop_at_boundary(text, start, end, boundary_regex)
    raw = text[start:cropped_end].rstrip()
    cleaned = clean_name_text(raw)
    if not cleaned:
        return None
    return (cleaned, start, start + len(raw))


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
