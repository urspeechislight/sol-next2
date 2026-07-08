"""Validate reliability grades against their cited source page and build reader links.

The sol-next rijal extraction scraped grading words at page level and misattributed
them (a page holds several narrators, and books such as Maʿrifat al-Thiqat label each
verdict ``قول <critic>``). This module reads the cited page, isolates the narrator's own
entry, splits it into per-critic segments by the ``قول`` markers (the book's author owns
the head segment before any ``قول``), and keeps a grade only when its term actually sits
in the segment of the critic it is attributed to. A surviving grade carries a relative,
URL-independent reader deep-link to exactly where it is recorded.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final
from urllib.parse import quote

from backend.patterns import normalize_arabic

_QAWL: Final[str] = "قول "
_ENTRY_WINDOW: Final[int] = 1600
_CRITIC_KEY_TOKENS: Final[int] = 2


def load_book_pages(path: Path) -> dict[int, str]:
    """Return ``{page_number: text}`` for one source book, or empty if unreadable."""
    if not path.exists():
        return {}
    book = json.load(path.open(encoding="utf-8"))
    pages: dict[int, str] = {}
    for section in book.get("content", {}).values():
        for page in section:
            number = page.get("page_number")
            if isinstance(number, int):
                pages[number] = page.get("content", "") or ""
    return pages


def _narrator_entry(page_text: str, name: str) -> str:
    """Isolate the narrator's entry region on the page, anchored on the first name tokens."""
    tokens = name.split()
    anchor = " ".join(tokens[:_CRITIC_KEY_TOKENS]) if len(tokens) >= _CRITIC_KEY_TOKENS else name
    index = page_text.find(anchor)
    if index < 0:
        return ""
    return page_text[index : index + _ENTRY_WINDOW]


def _segments(entry_text: str, book_author: str) -> dict[str, str]:
    """Split an entry into ``{critic: verdict_text}`` by ``قول`` markers; author owns the head."""
    parts = entry_text.split(_QAWL)
    out: dict[str, str] = {}
    if book_author:
        out[normalize_arabic(book_author)] = parts[0]
    for part in parts[1:]:
        critic = part.split("\n", 1)[0].strip()
        out[normalize_arabic(critic)] = part
    return out


def _segment_for(evaluator: str, segments: dict[str, str]) -> str | None:
    """Find the segment whose critic label best matches the evaluator, or None."""
    ev = normalize_arabic(evaluator)
    ev_head = " ".join(ev.split()[:_CRITIC_KEY_TOKENS])
    for critic, text in segments.items():
        if critic == ev or critic.startswith(ev_head) or ev_head in critic:
            return text
    return None


def validate_grade(pages: dict[int, str], grade: dict[str, Any], name: str) -> bool:
    """True when the grade's term sits in its evaluator's segment of the cited page's entry."""
    src = grade.get("source") or {}
    page, term, evaluator = src.get("page"), grade.get("term"), grade.get("evaluator")
    if not (isinstance(page, int) and term and evaluator):
        return False
    entry = _narrator_entry(pages.get(page, ""), name)
    if not entry:
        return False
    segment = _segment_for(evaluator, _segments(entry, src.get("author") or ""))
    return segment is not None and normalize_arabic(term) in normalize_arabic(segment)


def deep_link(work_id: str, page: int, name: str) -> str:
    """A relative, URL-independent reader link to where a grade is recorded."""
    return f"#/read/{work_id}/{page}?q={quote(name)}"
