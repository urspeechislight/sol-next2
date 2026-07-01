"""Tests for reader.get_page hadith serving (the M4 wiring point).

get_page combines SOL source (raw text, chapter title) with manuscript.hadiths_
for_page (structured hadiths). These pin the mutual-exclusivity contract: when
hadiths are present text_ar is None; otherwise the raw text is served.
"""

from __future__ import annotations

import pytest

from backend.models.reader import Hadith
from backend.repositories.reader import PageRow, get_page


def _fake_page_rows(_urn: str) -> list[PageRow]:
    """A single raw page row, standing in for the SOL source read."""
    return [PageRow(page=1, content="النص الخام")]


def _fake_chapter_title(*_args: object, **_kwargs: object) -> str:
    """An empty chapter title so get_page needs no real TOC source."""
    return ""


def _patch_page(monkeypatch: pytest.MonkeyPatch, *, hadiths: list[Hadith]) -> None:
    """Stub page_rows + _chapter_title_at + hadiths_for_page for get_page."""

    def fake_hadiths(_urn: str, _page: int) -> list[Hadith]:
        return hadiths

    monkeypatch.setattr("backend.repositories.reader.page_rows", _fake_page_rows)
    monkeypatch.setattr("backend.repositories.reader._chapter_title_at", _fake_chapter_title)
    monkeypatch.setattr("backend.repositories.manuscript.hadiths_for_page", fake_hadiths)


def test_should_serve_hadiths_with_null_text_when_page_is_extracted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hadith = Hadith(n=1, isnad_ar="الإسناد", matn_ar="المتن", narrators=[])
    _patch_page(monkeypatch, hadiths=[hadith])

    page = get_page("urn:test", 1)

    assert page.hadiths == [hadith]
    assert page.text_ar is None


def test_should_serve_raw_text_when_page_has_no_hadiths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_page(monkeypatch, hadiths=[])

    page = get_page("urn:test", 1)

    assert page.hadiths == []
    assert page.text_ar == "النص الخام"
