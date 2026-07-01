"""Smoke tests for the ported segment phase.

These run segment() end-to-end (config load -> compile -> split -> merge -> detect
-> route -> hierarchy -> emit) and assert the structural contract every span must
meet. Behavior-specific routing regressions (the gold set) land in a later test.
"""

from __future__ import annotations

from backend.pipeline.config import load_config
from backend.pipeline.models import Manuscript, ManuscriptPage
from backend.pipeline.segment import segment


def _manuscript() -> Manuscript:
    """A two-page manuscript exercising a heading, a hadith chain, and prose."""
    pages = [
        ManuscriptPage(
            page_number=1,
            page_name="1",
            text="كتاب الإيمان\nحدثنا محمد بن إسماعيل عن مالك بن أنس قال: إنما الأعمال بالنيات",
            is_content=True,
        ),
        ManuscriptPage(
            page_number=2,
            page_name="2",
            text="باب فضائل العلم\nوهذا شرح عام في الموضوع يذكر فيه فوائد كثيرة.",
            is_content=True,
        ),
    ]
    return Manuscript(
        work_id="w1",
        manifestation_id="m1",
        pages=pages,
        metadata={"book_type": "hadith", "toc": []},
    )


def test_should_emit_spans_with_behavior_and_hierarchy_when_segmenting() -> None:
    manuscript = _manuscript()
    config = load_config()
    result = segment(manuscript, config)
    assert result.spans, "segment produced no spans"
    for span in result.spans:
        assert span.behavior is not None, f"{span.span_id} has no behavior"
        assert span.hierarchy is not None, f"{span.span_id} has no hierarchy"
        assert span.span_type == "paragraph"
