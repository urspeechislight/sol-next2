"""Pattern detection + heading/content splitting for the segment phase.

detect_patterns runs every compiled detector against a span and emits one
Pattern per match (a single pattern_id can yield several when its regex matches
more than once). split_heading_from_content separates a heading marker from the
attribution content that follows it on the same line, so the content receives
its own behavior label instead of being absorbed into one SECTION_HEADING span.

Ported from sol-next's src/phases/segment.py (the detection half), split out to
keep segment.py under the file-size cap. Compiled patterns arrive ready-made
from the central pattern module; this module imports no regex machinery.
"""

from __future__ import annotations

from backend.core.constants import HADITH__SUBSECTION_HEADING_MAX_CHARS
from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.models import Pattern

_SUBSECTION_HEADING_LINE_REGEX: CompiledPattern = cached_compile(
    rf"^\*\s+([^\n]{{2,{HADITH__SUBSECTION_HEADING_MAX_CHARS}}})\n"
)


def detect_patterns(text: str, compiled_patterns: dict[str, CompiledPattern]) -> list[Pattern]:
    """Run all compiled pattern detectors against a span's text.

    Every regex match produces a Pattern object carrying its matched slice and
    character offsets, so later phases can build evidence anchors from it.
    """
    detected: list[Pattern] = []
    for pattern_id, compiled_regex in compiled_patterns.items():
        for match in compiled_regex.finditer(text):
            detected.append(
                Pattern(
                    pattern_id=pattern_id,
                    matched_text=match.group(),
                    char_start=match.start(),
                    char_end=match.end(),
                )
            )
    return detected


def split_heading_from_content(
    paragraphs: list[tuple[str, int, int]],
    heading_regex: CompiledPattern,
    attribution_strong_regex: CompiledPattern,
    min_heading_chars: int,
) -> list[tuple[str, int, int]]:
    """Split paragraphs where a heading marker precedes attribution content.

    Two modes: a classical heading keyword (باب/كتاب/فصل) sharing a line with
    the start of a hadith chain — splits where ATTRIBUTION_STRONG begins, only
    when the heading portion is at least min_heading_chars long; and a modern
    asterisk subsection (``* X :``) on its own line followed by narrative
    content — splits at the first newline so the content gets its own behavior.
    """
    result: list[tuple[str, int, int]] = []
    for text, page_start, page_end in paragraphs:
        subsection = _split_subsection(text, page_start, page_end)
        if subsection is not None:
            result.extend(subsection)
            continue
        heading_match = heading_regex.match(text)
        if heading_match is None:
            result.append((text, page_start, page_end))
            continue
        attr_match = attribution_strong_regex.search(text, pos=heading_match.end())
        if attr_match is None:
            result.append((text, page_start, page_end))
            continue
        heading_text = text[: attr_match.start()].rstrip()
        if len(heading_text) < min_heading_chars:
            result.append((text, page_start, page_end))
            continue
        result.append((heading_text, page_start, page_end))
        result.append((text[attr_match.start() :], page_start, page_end))
    return result


def _split_subsection(
    text: str, page_start: int, page_end: int
) -> list[tuple[str, int, int]] | None:
    """Split a ``* heading :`` subsection line from its following content.

    Returns the [heading, content] pair when the text opens with an asterisk
    subsection heading that has non-empty content after it; None otherwise.
    """
    sub_match = _SUBSECTION_HEADING_LINE_REGEX.match(text)
    if sub_match is None:
        return None
    heading_text = text[: sub_match.end()].rstrip()
    stripped_content = text[sub_match.end() :].strip()
    if not stripped_content:
        return None
    return [
        (heading_text, page_start, page_end),
        (stripped_content, page_start, page_end),
    ]
