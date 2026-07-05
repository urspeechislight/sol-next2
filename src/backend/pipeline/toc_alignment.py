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

import re
from bisect import bisect_left
from dataclasses import dataclass
from typing import Any, Final

from backend.core.logging import get_logger
from backend.patterns import CompiledPattern, cached_compile, escape_pattern, fold_search
from backend.pipeline.models import ManuscriptPage

_logger = get_logger("shia-library.toc-alignment")

TOC__DECORATION_RE: Final[CompiledPattern] = cached_compile(r"[\[\](){}«»\*]")
TOC__HONORIFIC_RE: Final[CompiledPattern] = cached_compile(r"[﵀-﵏ﷺﷻ]")
TOC__WHITESPACE_RE: Final[CompiledPattern] = cached_compile(r"\s+")
TOC__MIN_TITLE_WORDS: Final[int] = 1
TOC__MIN_TITLE_CHARS: Final[int] = 3
TOC__MIN_PREFIX_WORDS: Final[int] = 3
TOC__MIN_PREFIX_CHARS: Final[int] = 10
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


AnchoredParagraph = tuple[str, int, int, "TocAnchor | None"]
"""A segment paragraph carrying its TOC anchor (or None) through the split/merge
transforms, so the anchor rides with the heading text instead of being looked up
by a paragraph tuple those transforms rewrite."""


def normalize_for_match(text: str) -> str:
    """Strip decorations, honorifics, and diacritics, fold letter variants, collapse whitespace.

    Folding the alef/ya/taa letter variants (via the corpus search fold) is what
    lets a TOC title spelled نفي match a printed heading spelled نفى, and وإبطال
    match وابطال. Without it, hamza-seat and alef-maqsura spelling differences
    between the editorial TOC and the typeset body silently defeat every anchor
    in books that spell them differently (the whole reason Bihar anchored 0/20).
    """
    text = TOC__DECORATION_RE.sub(" ", text)
    text = TOC__HONORIFIC_RE.sub(" ", text)
    text = fold_search(text)
    return TOC__WHITESPACE_RE.sub(" ", text).strip()


def _fold_combined_text(combined_text: str) -> tuple[str, list[int]]:
    """Fold combined_text for anchor search, returning the fold and its index map.

    The fold matches :func:`normalize_for_match` per character (decorations and
    honorifics become spaces, diacritics drop, letter variants fold) so a title
    regex built from a normalized title can be searched directly against it.
    ``index_map[i]`` is the position in the original text of folded char ``i``,
    so a match offset in the fold converts back to the raw combined-text offset
    the anchor boundary needs. Diacritics are dropped rather than spaced so a
    vowel mark printed inside a word does not break the word for matching.
    """
    folded_chars: list[str] = []
    index_map: list[int] = []
    for i, ch in enumerate(combined_text):
        if TOC__DECORATION_RE.match(ch) or TOC__HONORIFIC_RE.match(ch):
            folded_chars.append(" ")
            index_map.append(i)
            continue
        folded = fold_search(ch)
        if not folded:
            continue
        folded_chars.append(folded)
        index_map.append(i)
    return "".join(folded_chars), index_map


def _title_words(title: str) -> list[str] | None:
    """Normalized title words, or None when the title is too short to anchor.

    That None is an explicit "not anchorable" signal, not a silent gap.
    """
    words = [w for w in normalize_for_match(title).split(" ") if w]
    if len(words) < TOC__MIN_TITLE_WORDS or len("".join(words)) < TOC__MIN_TITLE_CHARS:
        return None
    return words


def _title_prefixes(words: list[str]) -> list[list[str]]:
    """Word-prefixes of a title to try, longest first, down to the distinctness floor.

    A TOC title routinely appends a descriptive tail the printed heading omits
    (باب ٣ القضاء والقدر ... وفيه ٧٩ حديثا — "containing 79 hadiths"), so the full
    title fails while its distinctive head matches. Trying longest-first keeps
    the match as specific as the text supports; the floor (min prefix words and
    chars) stops a short head like باب ٣ from matching a spurious earlier
    mention. A title already below the floor is returned whole, since it is as
    specific as it gets.
    """
    prefixes: list[list[str]] = []
    for end in range(len(words), TOC__MIN_PREFIX_WORDS - 1, -1):
        prefix = words[:end]
        if len("".join(prefix)) < TOC__MIN_PREFIX_CHARS:
            break
        prefixes.append(prefix)
    if not prefixes:
        prefixes.append(words)
    return prefixes


def _match_title_prefix(
    folded_text: str, words: list[str], folded_lo: int, folded_hi: int
) -> re.Match[str] | None:
    """Longest word-prefix of the title that matches within the folded window.

    Words join with ``\\s+`` so typesetting whitespace does not defeat the match.
    """
    for prefix in _title_prefixes(words):
        pattern = r"\s+".join(escape_pattern(w) for w in prefix)
        match = cached_compile(pattern).search(folded_text, pos=folded_lo, endpos=folded_hi)
        if match is not None:
            return match
    return None


def _expand_entries(toc_entries: list[dict[str, Any]]) -> list[tuple[int, str]]:
    """Flatten TOC entries into (page_number, title) pairs, one per printed line.

    A single TOC entry sometimes carries two merged headings separated by a
    newline (``* أبواب العدل *\\nباب 1 نفي الظلم``): the source folded a section
    label and its first chapter into one row. Each line is a distinct heading in
    the body, so each becomes its own anchor candidate at the entry's page. An
    entry with a blank title or no page is dropped here.
    """
    pairs: list[tuple[int, str]] = []
    for entry in toc_entries:
        page_number = entry.get("page_number")
        title = (entry.get("title") or "").strip()
        if not title or page_number is None:
            continue
        for raw_line in title.split("\n"):
            line = raw_line.strip()
            if line:
                pairs.append((page_number, line))
    return pairs


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

    folded_text, index_map = _fold_combined_text(combined_text)
    page_num_to_idx = {p.page_number: i for i, p in enumerate(pages_list)}
    anchors: list[TocAnchor] = []
    skipped_count = 0
    for page_number, title in _expand_entries(toc_entries):
        words = _title_words(title)
        if words is None:
            skipped_count += 1
            continue
        center_idx = page_num_to_idx.get(page_number)
        if center_idx is None:
            skipped_count += 1
            continue
        lo_idx = max(0, center_idx - TOC__MAX_PAGE_DRIFT)
        hi_idx = min(len(pages_list) - 1, center_idx + TOC__MAX_PAGE_DRIFT)
        raw_lo = page_starts[lo_idx]
        raw_hi = page_starts[hi_idx + 1] if hi_idx + 1 < len(page_starts) else len(combined_text)
        folded_lo = bisect_left(index_map, raw_lo)
        folded_hi = bisect_left(index_map, raw_hi)
        match = _match_title_prefix(folded_text, words, folded_lo, folded_hi)
        if match is None:
            skipped_count += 1
            continue
        anchors.append(
            TocAnchor(
                char_offset=index_map[match.start()],
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
