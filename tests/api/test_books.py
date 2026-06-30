"""Tests for ``GET /api/books`` (paginated) and ``GET /api/books/{urn}``."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.core.constants import BOOK__DEATH_YEAR_AH_MAX, HTTP__DEFAULT_PAGE_SIZE
from backend.models.book import Book
from backend.repositories import books as books_repo
from backend.repositories._data_loader import DataLoadError

EXPECTED_INDEX_MIN_COUNT = 1000
PAGINATION_CUSTOM_LIMIT = 10
PAGINATION_OFFSET_SAMPLE = 5

# A stable URN from the ingested index. Picked from the first arabic-language
# -sciences entry which is the alphabetically-first category.
SAMPLE_BOOK_URN = "sY-50TSO"


def test_should_return_paginated_envelope_when_listing(client: TestClient) -> None:
    """`/api/books` returns {items, total, limit, offset}."""
    response = client.get("/api/books")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"items", "total", "limit", "offset"}
    assert payload["limit"] == HTTP__DEFAULT_PAGE_SIZE
    assert payload["offset"] == 0


def test_should_index_more_than_a_thousand_books(client: TestClient) -> None:
    """Real corpus ingest should index ~18k books; assert a comfortable floor."""
    response = client.get("/api/books")
    payload = response.json()
    assert payload["total"] >= EXPECTED_INDEX_MIN_COUNT


def test_should_respect_limit_parameter(client: TestClient) -> None:
    """`?limit=N` caps items at N."""
    response = client.get("/api/books", params={"limit": PAGINATION_CUSTOM_LIMIT})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == PAGINATION_CUSTOM_LIMIT
    assert payload["limit"] == PAGINATION_CUSTOM_LIMIT


def test_should_respect_offset_parameter(client: TestClient) -> None:
    """`?offset=N` skips N records; total unchanged."""
    first_page = client.get("/api/books", params={"limit": PAGINATION_CUSTOM_LIMIT}).json()
    offset_page = client.get(
        "/api/books",
        params={"limit": PAGINATION_CUSTOM_LIMIT, "offset": PAGINATION_OFFSET_SAMPLE},
    ).json()
    assert first_page["total"] == offset_page["total"]
    assert first_page["items"][PAGINATION_OFFSET_SAMPLE]["urn"] == offset_page["items"][0]["urn"]


def test_should_filter_books_by_category_when_given(client: TestClient) -> None:
    """`?category=hanafi-fiqh` narrows results to that category."""
    response = client.get("/api/books", params={"category": "hanafi-fiqh"})
    assert response.status_code == 200
    payload = response.json()
    assert all(book["category"] == "hanafi-fiqh" for book in payload["items"])
    assert payload["total"] >= 1


def test_should_return_book_detail_when_urn_known(client: TestClient) -> None:
    """A known URN returns the full book record."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["urn"] == SAMPLE_BOOK_URN
    assert payload["title_ar"]


def test_should_return_404_when_urn_unknown(client: TestClient) -> None:
    """An unknown URN yields a 404 with a helpful detail."""
    response = client.get("/api/books/no-such-book")
    assert response.status_code == 404
    assert "no-such-book" in response.json()["detail"]


def test_should_serialize_arabic_title_round_trip(client: TestClient) -> None:
    """Arabic titles round-trip without mojibake."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}")
    payload = response.json()
    assert any("؀" <= c <= "ۿ" for c in payload["title_ar"])


def test_should_raise_when_index_missing_books_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """A wrong-shape index fails loud instead of serving an empty catalogue."""

    def _without_books_key(_name: str) -> dict[str, object]:
        return {"sources": {}}

    books_repo._index.cache_clear()
    monkeypatch.setattr(books_repo, "load_json", _without_books_key)
    with pytest.raises(DataLoadError):
        books_repo._index()
    books_repo._index.cache_clear()


def test_should_allow_unranked_canonical_to_be_null() -> None:
    """An unranked book is None, not a fabricated 'primary' (top rank)."""
    book = Book(urn="x", title_ar="ت", author_ar="م", category="c", canonical=None)
    assert book.canonical is None


def test_should_reject_death_year_above_bound() -> None:
    """A death year at/above the bound — where the upstream 99999 'unknown'
    sentinel sits — is rejected rather than served as a real far-future date."""
    with pytest.raises(ValidationError):
        Book(
            urn="x",
            title_ar="ت",
            author_ar="م",
            category="c",
            death_year_ah=BOOK__DEATH_YEAR_AH_MAX + 1,
        )
