"""Tests for ``GET /api/search/books`` — book metadata search by title/author."""

from __future__ import annotations

from fastapi.testclient import TestClient

AUTHOR = "الكليني"
SAMPLE_LIMIT = 3


def test_should_find_books_by_author_when_field_author(client: TestClient) -> None:
    """`field=author` returns books by a matching author, shaped as Book."""
    payload = client.get(
        "/api/search/books", params={"q": AUTHOR, "field": "author", "limit": SAMPLE_LIMIT}
    ).json()
    assert payload["total"] >= 1
    item = payload["items"][0]
    assert set(item.keys()) >= {"urn", "title_ar", "author_ar", "category"}
    assert AUTHOR in item["author_ar"]


def test_should_match_latin_when_field_any(client: TestClient) -> None:
    """A Latin query matches title_en/author lower-cased (field=any)."""
    payload = client.get("/api/search/books", params={"q": "kafi", "field": "any"}).json()
    assert payload["total"] >= 1


def test_should_return_empty_books_when_query_blank(client: TestClient) -> None:
    """A blank query yields no books rather than the whole catalogue."""
    payload = client.get("/api/search/books", params={"q": ""}).json()
    assert payload["total"] == 0
    assert payload["items"] == []
