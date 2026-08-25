"""Tests for the proxied cross-corpus search.

The reader forwards /api/search and /api/search/facets to the consolidated search
backend, so these tests fix the backend's JSON shape with a local mock transport
and assert the proxy maps it onto CorpusMatch / SearchFacets and forwards the
scope params. Repository-level tests call the proxy directly (async) to assert
forwarding and mapping free of the HTTP edge; the API-level tests cover the edge
serialization and the unknown-mode rejection.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.repositories import corpus as corpus_repo


def _hit(**over: Any) -> dict[str, Any]:
    """One backend SearchHit, with any field overridden by ``over``."""
    base: dict[str, Any] = {
        "page_id": 11,
        "urn": "abc123",
        "title_ar": "كتاب",
        "title_en": "Book",
        "author": "Author",
        "category": "hadith",
        "volume": 1,
        "stem": "abc123",
        "page_number": 5,
        "snippet": "…<b>نص</b>…",
    }
    base.update(over)
    return base


def _json_page() -> dict[str, Any]:
    """The canned /api/search response: one hit and a bounded total."""
    return {"items": [_hit()], "limit": 24, "next_after": None, "total": 7}


def _json_facets() -> dict[str, Any]:
    """The canned /api/search/facets response: one of each facet kind."""
    return {
        "categories": [{"slug": "hadith", "count": 7}],
        "books": [{"title": "كتاب", "title_en": "Book", "count": 3}],
        "volumes": [{"volume": 1, "count": 2}],
    }


@pytest.fixture
def backend(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    """Point the proxy at a mock backend and record every request it sends.

    Returns the captured request list so a test can assert forwarded scope params.
    ``/api/search`` returns one hit plus a bounded total; ``/api/search/facets``
    returns one category, one book, one volume.
    """
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        """Record the request and return the canned page or facets JSON for its path."""
        requests.append(request)
        if request.url.path == "/api/search":
            return httpx.Response(200, json=_json_page())
        return httpx.Response(200, json=_json_facets())

    client = httpx.AsyncClient(
        base_url="http://backend.test",
        transport=httpx.MockTransport(handler),
    )
    monkeypatch.setattr(corpus_repo, "_client", lambda: client)
    return requests


@pytest.mark.asyncio
async def test_should_map_hits_and_bounded_total_when_searching(
    backend: list[httpx.Request],
) -> None:
    """search() maps a backend hit onto CorpusMatch (page from page_number) + total."""
    matches, total = await corpus_repo.search(corpus_repo.SearchQuery(q="نص"))
    assert total == 7
    assert len(matches) == 1
    first = matches[0]
    assert first.urn == "abc123"
    assert first.page == 5
    assert len(backend) == 1


@pytest.mark.asyncio
async def test_should_map_hit_metadata_when_searching(backend: list[httpx.Request]) -> None:
    """The mapped CorpusMatch carries the backend title/author/category/volume."""
    matches, _total = await corpus_repo.search(corpus_repo.SearchQuery(q="نص"))
    first = matches[0]
    assert first.title_en == "Book"
    assert first.title_ar == "كتاب"
    assert first.author == "Author"
    assert first.category == "hadith"
    assert first.volume == 1
    assert len(backend) == 1


@pytest.mark.asyncio
async def test_should_strip_markup_tags_from_backend_snippets(
    backend: list[httpx.Request],
) -> None:
    """The mapped snippet is plain text; FTS markup is the reader's job."""
    matches, _total = await corpus_repo.search(corpus_repo.SearchQuery(q="نص"))
    assert matches[0].snippet == "…نص…"
    assert len(backend) == 1


@pytest.mark.asyncio
async def test_should_forward_scope_to_backend_when_searching(backend: list[httpx.Request]) -> None:
    """Query, mode, category set, book, volume, paging, include_count are forwarded."""
    await corpus_repo.search(
        corpus_repo.SearchQuery(
            q="نص", mode="broad", categories=("hadith", "quran"), book="كتاب", volume=2
        ),
        limit=5,
        offset=10,
    )
    params = backend[-1].url.params
    assert params["q"] == "نص"
    assert params["mode"] == "broad"
    assert params["book"] == "كتاب"
    assert params["volume"] == "2"
    assert params["limit"] == "5"
    assert params["offset"] == "10"
    assert params["include_count"] == "true"
    assert params.get_list("category") == ["hadith", "quran"]


@pytest.mark.asyncio
async def test_should_short_circuit_search_when_query_is_blank(
    backend: list[httpx.Request],
) -> None:
    """A query that folds to nothing returns empty with no backend round-trip."""
    matches, total = await corpus_repo.search(corpus_repo.SearchQuery(q=""))
    assert matches == []
    assert total == 0
    assert backend == []


@pytest.mark.asyncio
async def test_should_raise_corpus_search_error_when_backend_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A backend failure raises CorpusSearchError rather than returning empty results."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Always return 503 so the proxy must surface a CorpusSearchError."""
        return httpx.Response(503)

    broken = httpx.AsyncClient(
        base_url="http://backend.test",
        transport=httpx.MockTransport(handler),
    )
    monkeypatch.setattr(corpus_repo, "_client", lambda: broken)
    with pytest.raises(corpus_repo.CorpusSearchError):
        await corpus_repo.search(corpus_repo.SearchQuery(q="نص"))


@pytest.mark.asyncio
async def test_should_map_and_forward_scope_when_faceting(backend: list[httpx.Request]) -> None:
    """facets() maps categories/books/volumes and forwards mode, category, book."""
    facets = await corpus_repo.facets(q="نص", mode="broad", categories=("hadith",), book="كتاب")
    params = backend[-1].url.params
    assert params["mode"] == "broad"
    assert params["book"] == "كتاب"
    assert params.get_list("category") == ["hadith"]
    assert [(c.slug, c.count) for c in facets.categories] == [("hadith", 7)]
    assert [(b.title, b.count) for b in facets.books] == [("كتاب", 3)]
    assert [(v.volume, v.count) for v in facets.volumes] == [(1, 2)]


@pytest.mark.asyncio
async def test_should_short_circuit_facets_when_query_is_blank(
    backend: list[httpx.Request],
) -> None:
    """A blank facets query returns empty facets with no backend round-trip."""
    facets = await corpus_repo.facets(q="")
    assert facets.categories == []
    assert facets.books == []
    assert facets.volumes == []
    assert backend == []


def test_should_map_hit_onto_page_for_api_search(
    client: TestClient, backend: list[httpx.Request]
) -> None:
    """/api/search serializes the proxied hit with the reader page field set."""
    payload = client.get("/api/search", params={"q": "نص"}).json()
    assert payload["total"] == 7
    item = payload["items"][0]
    assert set(item.keys()) == {
        "urn",
        "title_ar",
        "title_en",
        "author",
        "category",
        "volume",
        "page",
        "snippet",
    }
    assert item["page"] == 5
    assert len(backend) == 1


def test_should_return_empty_page_when_api_query_is_blank(
    client: TestClient, backend: list[httpx.Request]
) -> None:
    """A blank query yields an empty page with no backend round-trip."""
    payload = client.get("/api/search", params={"q": ""}).json()
    assert payload["items"] == []
    assert payload["total"] == 0
    assert backend == []


def test_should_map_facets_onto_response_for_api(
    client: TestClient, backend: list[httpx.Request]
) -> None:
    """/api/search/facets serializes the proxied categories/books/volumes."""
    payload = client.get("/api/search/facets", params={"q": "نص"}).json()
    assert set(payload.keys()) == {"categories", "books", "volumes"}
    assert payload["categories"] == [{"slug": "hadith", "count": 7}]
    assert payload["books"] == [{"title": "كتاب", "title_en": "Book", "count": 3}]
    assert payload["volumes"] == [{"volume": 1, "count": 2}]
    assert len(backend) == 1


def test_should_return_422_when_mode_is_unknown(client: TestClient) -> None:
    """An out-of-set ?mode= is rejected at the edge, not forwarded to the backend."""
    response = client.get("/api/search", params={"q": "نص", "mode": "bogus"})
    assert response.status_code == 422
