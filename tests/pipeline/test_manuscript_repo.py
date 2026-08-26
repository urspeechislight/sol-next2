"""Tests for the manuscript read repo: the units/entities -> Hadith reshape.

Exercises the pure reshape (grouping, narrator ordering, sequence numbering) and
the absent-artifact guard, without a live manuscript.db.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.repositories.manuscript import (
    _EntityRow,
    _reshape_hadiths,
    _UnitRow,
    hadiths_for_page,
)


def test_should_reshape_isnad_matn_and_narrators_into_hadith() -> None:
    units = [
        _UnitRow(unit_id="urn_u0001", span_id="s1", unit_type="ISNAD_UNIT", text_ar="عن مالك"),
        _UnitRow(unit_id="urn_u0002", span_id="s1", unit_type="MATN_UNIT", text_ar="إنما الأعمال"),
    ]
    entities = [
        _EntityRow(
            span_id="s1",
            text_ar="مالك",
            role_in_context="narrator",
            chain_position=0,
            narrator_id=None,
        ),
    ]

    hadiths = _reshape_hadiths(units, entities)

    assert len(hadiths) == 1
    hadith = hadiths[0]
    assert hadith.n == 1
    assert hadith.isnad_ar == "عن مالك"
    assert hadith.matn_ar == "إنما الأعمال"
    assert [narrator.name_ar for narrator in hadith.narrators] == ["مالك"]
    assert hadith.narrators[0].grade == ""


def test_should_order_narrators_by_chain_position() -> None:
    units = [
        _UnitRow(unit_id="urn_u0001", span_id="s1", unit_type="ISNAD_UNIT", text_ar="isnad"),
        _UnitRow(unit_id="urn_u0002", span_id="s1", unit_type="MATN_UNIT", text_ar="matn"),
    ]
    entities = [
        _EntityRow(
            span_id="s1",
            text_ar="الثاني",
            role_in_context="narrator",
            chain_position=1,
            narrator_id=None,
        ),
        _EntityRow(
            span_id="s1",
            text_ar="الأول",
            role_in_context="narrator",
            chain_position=0,
            narrator_id=None,
        ),
    ]

    hadiths = _reshape_hadiths(units, entities)

    assert [narrator.name_ar for narrator in hadiths[0].narrators] == ["الأول", "الثاني"]


def test_should_assign_sequence_numbers_in_document_order() -> None:
    units = [
        _UnitRow(unit_id="urn_u0003", span_id="s2", unit_type="ISNAD_UNIT", text_ar="i2"),
        _UnitRow(unit_id="urn_u0004", span_id="s2", unit_type="MATN_UNIT", text_ar="m2"),
        _UnitRow(unit_id="urn_u0001", span_id="s1", unit_type="ISNAD_UNIT", text_ar="i1"),
        _UnitRow(unit_id="urn_u0002", span_id="s1", unit_type="MATN_UNIT", text_ar="m1"),
    ]

    hadiths = _reshape_hadiths(units, [])

    assert [hadith.n for hadith in hadiths] == [1, 2]
    assert [hadith.isnad_ar for hadith in hadiths] == ["i1", "i2"]


def test_should_skip_spans_without_isnad_or_matn_unit() -> None:
    units = [_UnitRow(unit_id="urn_u0001", span_id="s1", unit_type="PROSE_UNIT", text_ar="نص")]

    assert _reshape_hadiths(units, []) == []


def test_should_return_empty_when_manuscript_db_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_data_path(_name: str) -> Path:
        return Path("/nonexistent/manuscript.db")

    monkeypatch.setattr("backend.repositories.manuscript.data_path", fake_data_path)

    assert hadiths_for_page("urn:absent", 1) == []
