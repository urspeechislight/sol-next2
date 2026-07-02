"""TOC-to-text alignment for the segment phase.

Most Arabic books in the corpus ship with a rich embedded TOC (a flat list of
{page_number, title} entries). This module turns each TOC entry into a confirmed
character-offset boundary in the combined text, so segment can split spans at
TOC-confirmed positions and tag each span with the TOC title that opens it.
Books without a TOC rely entirely on pattern-based detection.

Failure modes are explicit: a TOC entry whose title cannot be located in its
declared page range is logged and skipped — wrong TOC data must not produce wrong
split positions. Ported from sol-next's src/utils/toc_alignment.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from backend.core.logging import get_logger
from backend.patterns import CompiledPattern, cached_compile, escape_pattern, strip_tashkeel
from backend.pipeline.models import ManuscriptPage

_logger = get_logger("shia-library.toc-alignment")

TOC__DECORATION_RE: Final[CompiledPattern] = cached_compile(r"[\[\](){}«»\*]")
TOC__HONORIFIC_RE: Final[CompiledPattern] = cached_compile(r"[﵀-﵏ﷺﷻ]")
TOC__WHITESPACE_RE: Final[CompiledPattern] = cached_compile(r"\s+")
TOC__MIN_TITLE_WORDS: Final[int] = 1
TOC__MIN_TITLE_CHARS: Final[int] = 3
TOC__MAX_PAGE_DRIFT: Final[int] = 2
TOC__LEAF_LEVEL: Final[int] = 3


@dataclass(frozen=True)
class TocAnchor:
    """A confirmed TOC-to-text alignment.

    char_offset is where the entry's content begins (the span boundary is placed
    just before it); level is an inferred structural depth (0 = top, higher =
    deeper; see infer_toc_level).
    """

    char_offset: int
    page_number: int
    title: str
    level: int


def normalize_for_match(text: str) -> str:
    """Strip decorations, honorifics, and diacritics, then collapse whitespace."""
    text = TOC__DECORATION_RE.sub(" ", text)
    text = TOC__HONORIFIC_RE.sub(" ", text)
    text = strip_tashkeel(text)
    return TOC__WHITESPACE_RE.sub(" ", text).strip()


def title_to_search_regex(title: str) -> CompiledPattern | None:
    """Compile a flexible-whitespace regex from a normalized TOC title.

    Words are separated by ``\\s+`` so OCR/typesetting whitespace does not break
    the match. Returns None when the title is too short to be a reliable anchor;
    that None is an explicit "not anchorable" signal, not a silent gap.
    """
    normalized = normalize_for_match(title)
    words = [w for w in normalized.split(" ") if w]
    if len(words) < TOC__MIN_TITLE_WORDS:
        return None
    if len("".join(words)) < TOC__MIN_TITLE_CHARS:
        return None
    pattern = r"\s+".join(escape_pattern(w) for w in words)
    return cached_compile(pattern)


def find_toc_anchors(
    combined_text: str,
    toc_entries: list[dict[str, Any]],
    page_starts: list[int],
    pages_list: list[ManuscriptPage],
) -> list[TocAnchor]:
    """Locate each TOC entry's title in combined_text and emit anchors.

    For each entry: build a flexible-whitespace search regex, restrict the search
    to the declared page's range (within TOC__MAX_PAGE_DRIFT pages to absorb
    off-by-one numbering), and use the first match's start as the anchor offset.
    Entries whose titles are too short, whose declared page is outside the
    manuscript, or whose title is not found are logged and skipped — never
    fabricated. Returns anchors sorted by offset, deduplicated by offset.
    """
    if not toc_entries or not page_starts:
        return []

    page_num_to_idx = {p.page_number: i for i, p in enumerate(pages_list)}
    anchors: list[TocAnchor] = []
    skipped_count = 0
    for entry in toc_entries:
        title = (entry.get("title") or "").strip()
        page_number = entry.get("page_number")
        if not title or page_number is None:
            skipped_count += 1
            continue
        regex = title_to_search_regex(title)
        if regex is None:
            skipped_count += 1
            continue
        center_idx = page_num_to_idx.get(page_number)
        if center_idx is None:
            skipped_count += 1
            continue
        lo_idx = max(0, center_idx - TOC__MAX_PAGE_DRIFT)
        hi_idx = min(len(pages_list) - 1, center_idx + TOC__MAX_PAGE_DRIFT)
        lo_offset = page_starts[lo_idx]
        hi_offset = page_starts[hi_idx + 1] if hi_idx + 1 < len(page_starts) else len(combined_text)
        match = regex.search(combined_text, pos=lo_offset, endpos=hi_offset)
        if match is None:
            skipped_count += 1
            continue
        anchors.append(
            TocAnchor(
                char_offset=match.start(),
                page_number=page_number,
                title=title,
                level=infer_toc_level(title),
            )
        )

    anchors.sort(key=lambda a: (a.char_offset, a.level))
    seen_offsets: set[int] = set()
    deduped: list[TocAnchor] = []
    for a in anchors:
        if a.char_offset in seen_offsets:
            continue
        seen_offsets.add(a.char_offset)
        deduped.append(a)

    if skipped_count:
        _logger.info(
            "toc-anchors-skipped",
            anchored=len(deduped),
            total=len(toc_entries),
            skipped=skipped_count,
        )
    return deduped


def infer_toc_level(title: str) -> int:
    """Infer the structural level of a TOC entry from its title shape.

    Coarse scale (lower = higher in tree): 0 = book/volume/research top-level
    ([X], الفن/كتاب X); 1 = section (باب/فصل/مقصد); 2 = subsection (asterisk
    prefix, or unmarked); 3 = leaf list item (numbered/lettered/ordinal).
    """
    stripped = title.strip()
    if stripped.startswith("["):
        return 0
    if cached_compile(r"^\s*(?:الفن|كتاب|الكتاب|مسند|قسم|القسم|جزء|الجزء)\b").match(stripped):
        return 0
    if stripped.startswith("*"):
        return 2
    leaf_numbered = cached_compile(r"^\s*(?:[٠-٩0-9]+|[أ-ي])\s*[\-\)]").match(stripped)
    leaf_ordinal = cached_compile(
        r"^\s*(?:أولا|ثانيا|ثالثا|رابعا|خامسا|سادسا|سابعا|ثامنا|تاسعا|عاشرا)\b"
    ).match(stripped)
    if leaf_numbered or leaf_ordinal:
        return TOC__LEAF_LEVEL
    if cached_compile(
        r"^\s*(?:باب|الباب|فصل|الفصل|مبحث|المبحث|مقصد|المقصد|مطلب|المطلب|مسألة|المسألة)\b"
    ).match(stripped):
        return 1
    return 2
