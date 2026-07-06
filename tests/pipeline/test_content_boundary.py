"""Tests for basmala-anchored content-boundary detection in the segment phase.

The classical text opens with the basmala; a modern editor's introduction
precedes it. Everything before the work's opening basmala is editorial
front-matter and must not be routed into extraction, even when the editor's
prose quotes transmission verbs (روى، عن) that would otherwise classify as a
hadith. But a basmala that opens an internal section of an already-started
collection (many hadith precede it) is not the work opener and must not bury the
content before it.
"""

from __future__ import annotations

from backend.pipeline.config import load_config
from backend.pipeline.models import Manuscript, ManuscriptPage
from backend.pipeline.segment import segment
from backend.pipeline.vocab import (
    HADITH__BEHAVIOR_EDITORIAL_FRONTMATTER,
    HADITH__BEHAVIOR_TRANSMISSION,
)

_HADITH = "أخبرنا محمد بن إسماعيل عن مالك بن أنس عن نافع عن ابن عمر قال قال رسول الله"


def _page(number: int, text: str) -> ManuscriptPage:
    """A content page carrying ``text`` at ``number``."""
    return ManuscriptPage(page_number=number, page_name=str(number), text=text, is_content=True)


def _segment(pages: list[ManuscriptPage]) -> dict[int, str | None]:
    """Segment a hadith-genre manuscript; return {page_start: behavior} for its spans."""
    manuscript = Manuscript(
        work_id="w",
        manifestation_id="m",
        pages=pages,
        metadata={"book_type": "hadith", "toc": []},
    )
    result = segment(manuscript, load_config())
    return {span.page_start: span.behavior for span in result.spans}


def test_should_mark_pre_basmala_editorial_prose_as_frontmatter() -> None:
    """Prose before the opening basmala is front-matter even when it reads as a chain."""
    by_page = _segment(
        [
            _page(1, "وروى المؤلف في مقدمته عن ابن سعد أخبارا في ترتيب هذا الكتاب"),
            _page(2, "بسم الله الرحمن الرحيم"),
            _page(3, _HADITH),
        ]
    )
    assert by_page[1] == HADITH__BEHAVIOR_EDITORIAL_FRONTMATTER
    assert by_page[3] == HADITH__BEHAVIOR_TRANSMISSION


def test_should_not_bury_content_before_an_internal_basmala() -> None:
    """A basmala preceded by many hadith opens an internal section, not the work."""
    pages = [_page(index + 1, _HADITH) for index in range(5)]
    pages.append(_page(6, "بسم الله الرحمن الرحيم"))
    pages.append(_page(7, _HADITH))
    by_page = _segment(pages)
    assert by_page[1] == HADITH__BEHAVIOR_TRANSMISSION
    assert by_page[5] == HADITH__BEHAVIOR_TRANSMISSION
