"""Tests for the reader endpoints: TOC + page content from corpus sources."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.core.errors import ResourceNotFoundError
from backend.repositories import reader as reader_repo

SAMPLE_BOOK_URN = "sY-50TSO"
SAMPLE_FIRST_PAGE = 1
MIN_TOC_ENTRIES = 1
MIN_PAGE_BODY_CHARS = 20
IN_BOOK_QUERY = "النحو"
_CANNED_PAGE_TEXT = "بسم الله الرحمن الرحيم هذه صفحة فيها نص عربي للتجربة"


@pytest.fixture
def page_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Serve a canned page for the sample book so the reader route needs no live backend.

    The reader route proxies page text through the consolidated backend's
    ``/api/r/page/{urn}/{n}``; this fixture points that client at a mock transport
    returning one canned page for the sample book's first page and 404 for any
    other, so the page-endpoint tests are independent of a co-deployed backend.
    """
    sample_path = f"/api/r/page/{SAMPLE_BOOK_URN}/{SAMPLE_FIRST_PAGE}"

    def handler(request: httpx.Request) -> httpx.Response:
        """Return page 1 JSON for the sample URN, 404 for any other page."""
        if request.url.path == sample_path:
            return httpx.Response(
                200,
                json={
                    "urn": SAMPLE_BOOK_URN,
                    "page_number": SAMPLE_FIRST_PAGE,
                    "text_ar": _CANNED_PAGE_TEXT,
                    "total_pages": 5,
                },
            )
        return httpx.Response(404)

    client = httpx.Client(
        base_url="http://backend.test",
        transport=httpx.MockTransport(handler),
    )
    monkeypatch.setattr(reader_repo, "_backend_client", lambda: client)


def test_should_return_toc_when_urn_known(client: TestClient) -> None:
    """A real ingested book exposes its TOC."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}/toc")
    assert response.status_code == 200
    payload = response.json()
    assert payload["book_urn"] == SAMPLE_BOOK_URN
    assert len(payload["entries"]) >= MIN_TOC_ENTRIES


def test_should_return_404_when_toc_urn_unknown(client: TestClient) -> None:
    """Unknown URN returns 404."""
    response = client.get("/api/books/no-such-book/toc")
    assert response.status_code == 404


def test_should_serve_text_when_first_page(
    client: TestClient,
    page_backend: None,  # noqa: ARG001
) -> None:
    """Page 1 of a real book serves its raw Arabic text; no parsed hadiths yet."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}/pages/{SAMPLE_FIRST_PAGE}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["page_number"] == SAMPLE_FIRST_PAGE
    assert payload["hadiths"] == []
    body = payload["text_ar"]
    assert len(body) >= MIN_PAGE_BODY_CHARS
    assert any("؀" <= c <= "ۿ" for c in body)


def test_should_keep_raw_text_when_no_hadith(
    client: TestClient,
    page_backend: None,  # noqa: ARG001
) -> None:
    """Pre-pipeline corpus pages carry raw text_ar, not a fabricated empty-isnad hadith."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}/pages/{SAMPLE_FIRST_PAGE}")
    payload = response.json()
    assert payload["hadiths"] == []
    assert payload["text_ar"] is not None
    assert len(payload["text_ar"]) >= MIN_PAGE_BODY_CHARS


def test_should_return_404_when_page_unknown(
    client: TestClient,
    page_backend: None,  # noqa: ARG001
) -> None:
    """A page beyond the book returns 404."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}/pages/999999")
    assert response.status_code == 404


def test_should_scope_search_to_one_book(client: TestClient) -> None:
    """In-book search returns page+snippet hits confined to the book, fewer than
    the same query across the whole corpus."""
    in_book = client.get(f"/api/books/{SAMPLE_BOOK_URN}/search", params={"q": IN_BOOK_QUERY}).json()
    assert in_book["total"] >= 1
    item = in_book["items"][0]
    assert set(item.keys()) == {"page", "snippet"}
    assert item["page"] >= 1 and item["snippet"]
    corpus_wide = client.get("/api/search", params={"q": IN_BOOK_QUERY, "limit": 1}).json()
    assert in_book["total"] <= corpus_wide["total"]


def test_should_return_empty_when_query_blank(client: TestClient) -> None:
    """A blank in-book query yields no matches rather than the whole book."""
    payload = client.get(f"/api/books/{SAMPLE_BOOK_URN}/search", params={"q": ""}).json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_should_yield_rows_when_book_known() -> None:
    """page_rows yields ordered (page, content) rows for a real book."""
    rows = reader_repo.page_rows(SAMPLE_BOOK_URN)
    assert rows
    assert rows[0].page >= 1
    assert rows[0].content


def test_should_raise_when_book_unknown() -> None:
    """An unknown URN raises rather than returning an empty page list."""
    with pytest.raises(ResourceNotFoundError):
        reader_repo.page_rows("no-such-book")


def test_should_raise_when_content_malformed() -> None:
    """A present-but-malformed content section raises, not masquerade as empty."""
    with pytest.raises(reader_repo.ReaderSourceError):
        reader_repo._content_rows({"content": "not-an-object"})
    with pytest.raises(reader_repo.ReaderSourceError):
        reader_repo._content_rows({"content": {"1": "not-a-list"}})


def test_should_return_empty_when_content_absent() -> None:
    """An absent content section is a legitimately page-less book, yielding []."""
    assert reader_repo._content_rows({}) == []


def test_should_raise_when_source_has_many_books() -> None:
    """A source file mapping more than one book is corruption, surfaced loudly."""
    with pytest.raises(reader_repo.ReaderSourceError):
        reader_repo._first_book_key({"1": [], "2": []})
