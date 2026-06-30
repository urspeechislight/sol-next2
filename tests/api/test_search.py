"""Tests for ``GET /api/search`` (cross-corpus full-text) + ``/api/search/facets``.

Runs against the real ``data/corpus.db`` built by
``scripts/build_corpus_index.py``, so assertions use floors, not exact counts.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

SAMPLE_LIMIT = 3
# A phrase present in the corpus (it is the title text on the first page of the
# alphabetically-first book, sY-50TSO).
KNOWN_PHRASE = "المصطلح النحوي"
# A common token that spans many categories + books, for the facet tests.
FACET_QUERY = "المصطلح"


def test_should_return_paginated_envelope_when_searching(client: TestClient) -> None:
    """`/api/search` returns {items, total, limit, offset}."""
    response = client.get("/api/search", params={"q": KNOWN_PHRASE, "limit": SAMPLE_LIMIT})
    assert response.status_code == 200
    assert set(response.json().keys()) == {"items", "total", "limit", "offset"}


def test_should_find_a_known_phrase_in_corpus(client: TestClient) -> None:
    """A phrase that exists in the corpus returns at least one shaped hit."""
    payload = client.get("/api/search", params={"q": KNOWN_PHRASE}).json()
    assert payload["total"] >= 1
    item = payload["items"][0]
    assert set(item.keys()) >= {"urn", "title_ar", "page", "snippet"}
    assert item["page"] >= 1
    assert item["snippet"]


def test_should_return_empty_when_query_blank(client: TestClient) -> None:
    """A blank query yields no matches rather than erroring."""
    payload = client.get("/api/search", params={"q": ""}).json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_should_cap_items_when_limit_given(client: TestClient) -> None:
    """`?limit=N` caps items at N."""
    payload = client.get("/api/search", params={"q": KNOWN_PHRASE, "limit": SAMPLE_LIMIT}).json()
    assert len(payload["items"]) <= SAMPLE_LIMIT


def test_should_return_drilldown_facets_when_querying(client: TestClient) -> None:
    """`/api/search/facets` returns categories (books/volumes are empty until
    their parent filter is set)."""
    payload = client.get("/api/search/facets", params={"q": FACET_QUERY}).json()
    assert set(payload.keys()) == {"categories", "books", "volumes"}
    assert payload["categories"]
    assert payload["books"] == []
    assert payload["volumes"] == []
    facet = payload["categories"][0]
    assert set(facet.keys()) == {"slug", "count"}
    assert facet["count"] >= 1


def test_should_scope_books_to_category_when_given(client: TestClient) -> None:
    """Passing a category surfaces the books (works) within it."""
    cats = client.get("/api/search/facets", params={"q": FACET_QUERY}).json()["categories"]
    slug = cats[0]["slug"]
    facets = client.get("/api/search/facets", params={"q": FACET_QUERY, "category": slug}).json()
    assert facets["books"]
    assert set(facets["books"][0].keys()) == {"title", "title_en", "count"}


def test_should_narrow_total_when_book_filtered(client: TestClient) -> None:
    """`?category=&book=` restricts results to that one book's pages."""
    cats = client.get("/api/search/facets", params={"q": FACET_QUERY}).json()["categories"]
    slug = cats[0]["slug"]
    books = client.get("/api/search/facets", params={"q": FACET_QUERY, "category": slug}).json()[
        "books"
    ]
    title = books[0]["title"]
    scoped = client.get(
        "/api/search", params={"q": FACET_QUERY, "category": slug, "book": title}
    ).json()
    in_cat = client.get("/api/search", params={"q": FACET_QUERY, "category": slug}).json()["total"]
    assert 0 < scoped["total"] <= in_cat


def test_should_reject_an_unknown_search_mode_with_422(client: TestClient) -> None:
    """An out-of-set ?mode= is rejected, not silently treated as exact."""
    response = client.get("/api/search", params={"q": KNOWN_PHRASE, "mode": "bogus"})
    assert response.status_code == 422


def test_should_reject_an_unknown_book_search_field_with_422(client: TestClient) -> None:
    """An out-of-set ?field= on /search/books is rejected, not treated as any."""
    response = client.get("/api/search/books", params={"q": "x", "field": "not-a-field"})
    assert response.status_code == 422
