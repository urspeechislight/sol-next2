"""Tests for the manuscript span artifact writer.

Segment a small manuscript, then assert (a) the row projection JSON-encodes each
span's structured fields correctly and (b) runner.create_artifact + the span
INSERT persist exactly one row per span. Persistence is checked via the
connection's total_changes counter rather than a SELECT, since raw SQL is not
permitted in tests (CENTRAL-005).
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.build import manuscript as manuscript_build
from backend.build import runner
from backend.pipeline.config import load_config
from backend.pipeline.models import Manuscript, ManuscriptPage
from backend.pipeline.segment import segment


def _segmented_manuscript() -> Manuscript:
    """A segmented two-page manuscript exercising a heading and a hadith chain."""
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
    manuscript = Manuscript(
        work_id="m1",
        manifestation_id="m1",
        pages=pages,
        metadata={"book_type": "hadith", "toc": []},
    )
    return segment(manuscript, load_config())


def test_should_project_and_persist_every_span(tmp_path: Path) -> None:
    manuscript = _segmented_manuscript()
    rows = manuscript_build.span_rows(manuscript)

    assert len(rows) == len(manuscript.spans)
    for row, span in zip(rows, manuscript.spans, strict=True):
        assert span.hierarchy is not None and span.behavior is not None
        assert row["span_id"] == span.span_id
        assert row["manifestation_id"] == manuscript.manifestation_id
        assert row["behavior"] == span.behavior
        assert row["hierarchy_depth"] == span.hierarchy.depth
        assert json.loads(row["hierarchy_path"]) == span.hierarchy.path
        pattern_ids = [pattern["pattern_id"] for pattern in json.loads(row["patterns"])]
        assert pattern_ids == [p.pattern_id for p in span.patterns]

    out = tmp_path / "manuscript.db"
    connection = runner.create_artifact(out, manuscript_build.MANUSCRIPT_SCHEMA)
    connection.executemany(manuscript_build.TABLES["span"], rows)
    assert connection.total_changes == len(manuscript.spans)
    connection.close()
