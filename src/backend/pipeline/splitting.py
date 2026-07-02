"""Text-splitting helpers for the segment phase.

Houses the boundary-splitter compiler, the page-aware text combiner, and the
chunk-then-paragraph splitter that produces the paragraph list segment operates
on. The TOC-aware variant accepts a sorted list of authoritative anchor offsets
and splits at those before applying the boundary regex within each chunk.
Framework-free: it knows about page text and character offsets, nothing about
behaviors, atomicizers, or extractors. Ported from sol-next's src/utils/splitting.py.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass
from typing import Any

from backend.core.logging import get_logger
from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.errors import SegmentError
from backend.pipeline.models import ManuscriptPage
from backend.pipeline.toc_alignment import TocAnchor

_logger = get_logger("shia-library.splitting")


def make_non_capturing(body: str) -> str:
    """Convert capturing groups to non-capturing, preserving [] character classes.

    A naive re.sub on ``(`` corrupts character classes like ``[\\s(*0-9]`` by
    injecting ``?:`` into the bracket expression. This parser copies bracket
    content verbatim (via _consume_char_class) and only converts ``(`` outside
    character classes.
    """
    out: list[str] = []
    i = 0
    n = len(body)
    while i < n:
        ch = body[i]
        if ch == "\\" and i + 1 < n:
            out.append(body[i : i + 2])
            i += 2
        elif ch == "[":
            token, i = _consume_char_class(body, i)
            out.append(token)
        elif ch == "(" and (i + 1 >= n or body[i + 1] != "?"):
            out.append("(?:")
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _consume_char_class(body: str, start: int) -> tuple[str, int]:
    """Consume a ``[...]`` character class starting at ``start``; return (token, next_i)."""
    n = len(body)
    j = start + 1
    if j < n and body[j] in ("^", "]"):
        j += 1
    while j < n and body[j] != "]":
        j += 2 if body[j] == "\\" and j + 1 < n else 1
    return body[start : j + 1], j + 1


def compile_boundary_splitter(raw_patterns: list[dict[str, Any]]) -> CompiledPattern:
    """Build the paragraph boundary splitter from config boundary patterns.

    Splits on a blank line (double newline) OR a single newline immediately
    before any pattern marked ``is_boundary: true`` in config. Raises
    SegmentError if a boundary pattern regex is invalid.
    """
    lookaheads: list[str] = []
    for entry in raw_patterns:
        if not entry.get("is_boundary"):
            continue
        body = make_non_capturing(entry["regex"].lstrip("^"))
        lookaheads.append(rf"[^\S\n]*(?:{body})")
    if not lookaheads:
        return cached_compile(r"\n\n")
    combined = "|".join(lookaheads)
    try:
        return cached_compile(rf"\n\n|\n(?={combined})", re.MULTILINE)
    except re.error as exc:
        raise SegmentError(f"Boundary splitter regex failed to compile: {exc}") from exc


def build_combined_text(
    content_pages: list[ManuscriptPage],
    name_prefix_tokens: frozenset[str],
    name_continuation_re: CompiledPattern,
) -> tuple[str, list[int], list[ManuscriptPage]]:
    """Concatenate content page texts with cross-page name repair.

    Pages join with ``\\n`` by default. When the previous page's last token is in
    name_prefix_tokens (عبد, أبو, ابن, ...) AND the next page begins with ال +
    an Arabic letter, pages join with a single space instead — this prevents
    compound names like عبد المطلب from being torn at the page boundary.
    """
    parts: list[str] = []
    page_starts: list[int] = []
    pages_list: list[ManuscriptPage] = []
    offset = 0
    for page in content_pages:
        if parts:
            prev_text = parts[-1]
            last_token = prev_text.rsplit(None, 1)[-1] if prev_text.strip() else ""
            sep = "\n"
            if last_token in name_prefix_tokens and name_continuation_re.match(page.text):
                sep = " "
                _logger.info("cross-page-name-repair", prev_token=last_token)
            parts.append(sep)
            offset += len(sep)
        page_starts.append(offset)
        pages_list.append(page)
        parts.append(page.text)
        offset += len(page.text)
    return "".join(parts), page_starts, pages_list


def page_number_at_offset(
    char_offset: int,
    page_starts: list[int],
    pages_list: list[ManuscriptPage],
) -> int:
    """Return the page_number of the page containing ``char_offset``."""
    idx = max(bisect.bisect_right(page_starts, char_offset) - 1, 0)
    return pages_list[idx].page_number


def _find_anchor_at(anchors: list[TocAnchor], offset: int) -> TocAnchor | None:
    """Return the TocAnchor whose char_offset equals ``offset``, or None."""
    for a in anchors:
        if a.char_offset == offset:
            return a
    return None


@dataclass(frozen=True, slots=True)
class SplitLayout:
    """Boundary regex + page layout + thresholds for split_with_page_tracking."""

    boundary_re: CompiledPattern
    page_starts: list[int]
    pages_list: list[ManuscriptPage]
    min_span_chars: int
    toc_anchors: list[TocAnchor] | None = None


def split_with_page_tracking(
    combined_text: str,
    layout: SplitLayout,
) -> list[tuple[str, int, int, TocAnchor | None]]:
    """Split combined text and map each paragraph to page range + TOC anchor.

    Two layers: forced splits at TOC anchor char_offsets (authoritative), then
    pattern-based splits via boundary_re within each chunk. The first paragraph
    in each chunk carries the corresponding TocAnchor; later paragraphs carry
    None.
    """
    anchors = list(layout.toc_anchors or [])
    chunk_bounds: list[tuple[int, int, TocAnchor | None]] = []
    prev = 0
    for a in anchors:
        if not (0 < a.char_offset < len(combined_text)):
            continue
        if a.char_offset > prev:
            anchor = _find_anchor_at(anchors, prev) if prev > 0 else None
            chunk_bounds.append((prev, a.char_offset, anchor))
        prev = a.char_offset
    tail_anchor = _find_anchor_at(anchors, prev) if prev > 0 else None
    chunk_bounds.append((prev, len(combined_text), tail_anchor))

    result: list[tuple[str, int, int, TocAnchor | None]] = []
    for lo, hi, anchor in chunk_bounds:
        chunk = combined_text[lo:hi]
        _emit_chunk_paragraphs(chunk, lo, layout, anchor, result)
    return result


def _emit_chunk_paragraphs(
    chunk: str,
    lo: int,
    layout: SplitLayout,
    anchor: TocAnchor | None,
    result: list[tuple[str, int, int, TocAnchor | None]],
) -> None:
    """Split one Layer-A chunk at the boundary regex and append its paragraphs to result."""
    parts = layout.boundary_re.split(chunk)
    search_from = 0
    first_paragraph_in_chunk = True
    for part in parts:
        if not part:
            continue
        idx = chunk.find(part, search_from)
        if idx == -1:
            idx = search_from
        stripped = part.strip()
        if stripped and len(stripped) >= layout.min_span_chars:
            strip_offset = part.index(stripped[0]) if stripped else 0
            text_start = lo + idx + strip_offset
            text_end = text_start + len(stripped) - 1
            pg_start = page_number_at_offset(text_start, layout.page_starts, layout.pages_list)
            pg_end = page_number_at_offset(text_end, layout.page_starts, layout.pages_list)
            attached = anchor if first_paragraph_in_chunk else None
            result.append((stripped, pg_start, pg_end, attached))
            first_paragraph_in_chunk = False
        search_from = idx + len(part)
