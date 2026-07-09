"""Synthesize a table of contents for books whose scraped TOC is empty or garbage.

Only high-precision detectors that read structure straight from the page body, so
every synthesized entry is grounded on its own page. A book with no clean
structure yields an empty result rather than a fabricated chapter list: naive
heading-keyword matching turns a prose ``كتاب الصلاة فأنا قرأته على مالك`` into a
false chapter, which is exactly what the reader is meant to stop showing.

* ``letters`` detects ``حرف X`` alphabetical section heads (dictionaries, indexes).
* ``numbered`` detects a monotonic ``N -`` entry sequence (rijal/biographical
  works), recovered as an LIS and gated by a page-spread guard so an incidental
  numbered list on one intro page cannot masquerade as book structure.

Regexes compile through :func:`backend.patterns.cached_compile` (CENTRAL-002).
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from typing import Any

from backend.core.constants import (
    TOC_SYNTH__LETTER_MIN,
    TOC_SYNTH__NUMBERED_MIN,
    TOC_SYNTH__NUMBERED_MIN_PAGES,
    TOC_SYNTH__NUMBERED_MIN_SPAN,
    TOC_SYNTH__TITLE_MAX_CHARS,
)
from backend.patterns import cached_compile

_LETTER_RE = cached_compile(r"(?:^|\n)\s*(حرف\s+(?:ال)?[ء-ي]{1,6})\s*(?:\n|:|$)")
_NUMBERED_RE = cached_compile(r"(?:^|\n)\s*(\d{1,4})\s*[-–]\s+(?=[^\W\d])")
_WHITESPACE_RE = cached_compile(r"\s+")


def _lis_indices(nums: list[int]) -> set[int]:
    """Return the indices of a longest strictly-increasing subsequence of ``nums``.

    The numbered-entry chain is recovered this way because footnote numbers,
    years, and cross-references also match the ``N -`` shape; a forward-tolerance
    filter cascades into mass rejection after one wide gap, whereas the LIS locks
    onto the dense ``+1`` spine and drops the stray numbers.
    """
    tails: list[int] = []
    tails_idx: list[int] = []
    prev = [-1] * len(nums)
    for k, x in enumerate(nums):
        j = bisect_left(tails, x)
        if j == len(tails):
            tails.append(x)
            tails_idx.append(k)
        else:
            tails[j] = x
            tails_idx[j] = k
        prev[k] = tails_idx[j - 1] if j > 0 else -1
    chain: set[int] = set()
    k = tails_idx[-1] if tails_idx else -1
    while k != -1:
        chain.add(k)
        k = prev[k]
    return chain


def _pages(content_rows: list[Any]) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...] for a source doc's content, page-ordered."""
    out: list[tuple[int, str]] = []
    for row in content_rows:
        if isinstance(row, dict) and isinstance(row.get("page_number"), int):
            out.append((row["page_number"], str(row.get("content") or "")))
    out.sort(key=lambda x: x[0])
    return out


def _detect_letters(pages: list[tuple[int, str]]) -> list[dict[str, Any]]:
    """Return distinct ``حرف X`` section heads, first page each, in page order."""
    first_page: dict[str, int] = {}
    for page_number, body in pages:
        for match in _LETTER_RE.finditer(body):
            title = _WHITESPACE_RE.sub(" ", match.group(1)).strip()
            if title not in first_page:
                first_page[title] = page_number
    ordered = sorted(first_page.items(), key=lambda item: item[1])
    return [{"page": page, "title": title} for title, page in ordered]


def _detect_numbered(pages: list[tuple[int, str]]) -> list[dict[str, Any]]:
    """Return a monotonic numbered-entry TOC, or [] when it is not book-wide."""
    parts: list[str] = []
    starts: list[int] = []
    page_of: list[int] = []
    cursor = 0
    for page_number, body in pages:
        starts.append(cursor)
        page_of.append(page_number)
        block = body + "\n"
        parts.append(block)
        cursor += len(block)
    text = "".join(parts)
    matches = list(_NUMBERED_RE.finditer(text))
    keep = _lis_indices([int(m.group(1)) for m in matches])
    entries: list[dict[str, Any]] = []
    for k, match in enumerate(matches):
        if k not in keep:
            continue
        end = matches[k + 1].start() if k + 1 < len(matches) else len(text)
        tail = _WHITESPACE_RE.sub(" ", text[match.end():end]).strip()
        title = tail.split(".")[0][:TOC_SYNTH__TITLE_MAX_CHARS].strip()
        page = page_of[bisect_right(starts, match.start()) - 1]
        entries.append({"page": page, "title": f"{match.group(1)} - {title}"})
    if not _book_wide(entries, len(pages)):
        return []
    return entries


def _book_wide(entries: list[dict[str, Any]], total_pages: int) -> bool:
    """True if entries span enough pages to be structure, not an incidental list."""
    if not entries:
        return False
    page_values = [e["page"] for e in entries]
    distinct = len(set(page_values))
    span = max(page_values) - min(page_values)
    return distinct >= TOC_SYNTH__NUMBERED_MIN_PAGES and span >= TOC_SYNTH__NUMBERED_MIN_SPAN * total_pages


def synthesize(content_rows: list[Any]) -> dict[str, Any]:
    """Return {'method', 'entries'} for a book, or method 'none' with no entries."""
    pages = _pages(content_rows)
    letters = _detect_letters(pages)
    if len(letters) >= TOC_SYNTH__LETTER_MIN:
        return {"method": "letters", "entries": letters}
    numbered = _detect_numbered(pages)
    if len(numbered) >= TOC_SYNTH__NUMBERED_MIN:
        return {"method": "numbered", "entries": numbered}
    return {"method": "none", "entries": []}
