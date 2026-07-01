"""Round-trip tests for the entity + unit writers (build/manuscript.py).

Segment + extract a small hadith manuscript, then assert the entity/unit row
projectors produce the right shapes and that runner.create_artifact + the
TABLES insert statements persist exactly (spans + entities + units) rows —
verified via the connection's total_changes counter, since raw SQL is not
permitted in tests (CENTRAL-005).
"""

from __future__ import annotations

from pathlib import Path

from backend.build import manuscript as manuscript_build
from backend.build import runner
from backend.pipeline.config import load_config
from backend.pipeline.extract import extract
from backend.pipeline.models import Manuscript, ManuscriptPage
from backend.pipeline.segment import segment

_CFG = load_config()


def _extracted_manuscript() -> Manuscript:
    """A one-page hadith manuscript run through segment then extract."""
    pages = [
        ManuscriptPage(
            page_number=1,
            page_name="1",
            text="كتاب الإيمان\nحدثنا محمد بن إسماعيل عن مالك بن أنس قال: إنما الأعمال بالنيات",
            is_content=True,
        )
    ]
    manuscript = Manuscript(
        work_id="urn:test",
        manifestation_id="urn:test",
        pages=pages,
        metadata={"book_type": "hadith", "toc": []},
    )
    return extract(segment(manuscript, _CFG), _CFG)


def test_should_project_nonempty_entity_and_unit_rows() -> None:
    rows_entity = manuscript_build.entity_rows(_extracted_manuscript())
    rows_unit = manuscript_build.unit_rows(_extracted_manuscript())

    assert rows_entity, "extract produced no entities"
    assert all(
        {"entity_id", "span_id", "text_ar", "metadata", "provenance", "evidence"} <= row.keys()
        for row in rows_entity
    )
    assert rows_unit, "extract produced no units"
    assert all(
        {"unit_id", "span_id", "unit_type", "text_ar", "metadata"} <= row.keys()
        for row in rows_unit
    )


def test_should_persist_spans_entities_and_units(tmp_path: Path) -> None:
    manuscript = _extracted_manuscript()
    con = runner.create_artifact(tmp_path / "manuscript.db", manuscript_build.MANUSCRIPT_SCHEMA)
    con.executemany(manuscript_build.TABLES["span"], manuscript_build.span_rows(manuscript))
    con.executemany(manuscript_build.TABLES["entity"], manuscript_build.entity_rows(manuscript))
    con.executemany(manuscript_build.TABLES["unit"], manuscript_build.unit_rows(manuscript))

    expected = len(manuscript.spans) + len(manuscript.entities) + len(manuscript.units)
    assert con.total_changes == expected
    con.close()
