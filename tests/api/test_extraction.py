"""Tests for the dev-gated ``/api/dev/extraction`` routes.

The books/pages assertions are artifact-agnostic (any built manuscript.db
satisfies them) so the suite does not pin which books were last extracted.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.api import extraction as extraction_api
from backend.core.settings import Settings, get_settings


def _patch_dev_tools(monkeypatch: pytest.MonkeyPatch, *, enabled: bool) -> None:
    """Pin the gate's settings view so tests never depend on the host .env."""
    pinned: Settings = get_settings().model_copy(update={"dev_tools": enabled})
    monkeypatch.setattr(extraction_api, "get_settings", lambda: pinned)


def test_should_return_404_on_every_route_when_dev_tools_are_off(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With SOL_DEV_TOOLS off the routes exist but answer 404, for everyone."""
    _patch_dev_tools(monkeypatch, enabled=False)
    assert client.get("/api/dev/extraction/books").status_code == 404
    assert client.get("/api/dev/extraction/books/any/pages/1").status_code == 404


def test_should_list_extracted_books_with_coverage(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The books list carries titles and non-degenerate coverage numbers."""
    _patch_dev_tools(monkeypatch, enabled=True)
    response = client.get("/api/dev/extraction/books")
    assert response.status_code == 200
    books = response.json()
    assert books
    for book in books:
        assert book["title_ar"]
        assert 1 <= book["first_page"] <= book["page_end"]
        assert book["spans"] > 0
        assert book["units"] > 0
        assert sum(b["units"] for b in book["behaviors"]) == book["units"]


def test_should_serve_one_page_near_raw(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A book's first extracted page yields spans whose units/entities join back."""
    _patch_dev_tools(monkeypatch, enabled=True)
    book = client.get("/api/dev/extraction/books").json()[0]
    response = client.get(f"/api/dev/extraction/books/{book['urn']}/pages/{book['first_page']}")
    assert response.status_code == 200
    page = response.json()
    assert page["book_urn"] == book["urn"]
    assert page["page_number"] == book["first_page"]
    assert page["spans"]
    span_ids = {span["span_id"] for span in page["spans"]}
    assert all(unit["span_id"] in span_ids for unit in page["units"])
    for span in page["spans"]:
        assert span["behavior"]
        assert isinstance(span["hierarchy_path"], list)
        for pattern in span["patterns"]:
            assert pattern["pattern_id"]


def test_should_return_404_when_urn_is_unknown(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An URN absent from the artifact 404s instead of returning empty lists."""
    _patch_dev_tools(monkeypatch, enabled=True)
    response = client.get("/api/dev/extraction/books/not-a-real-urn/pages/1")
    assert response.status_code == 404
