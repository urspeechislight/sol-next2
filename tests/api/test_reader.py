"""Tests for the reader endpoints: TOC + page content from corpus sources."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.core.errors import ResourceNotFoundError
from backend.repositories import reader as reader_repo

SAMPLE_BOOK_URN = "sY-50TSO"
SAMPLE_FIRST_PAGE = 1
MIN_TOC_ENTRIES = 1
MIN_PAGE_BODY_CHARS = 20
# A word present in the sample book (a grammar text), for in-book search.
IN_BOOK_QUERY = "النحو"


def test_should_return_toc_when_urn_known(client: TestClient) -> None:
    """A real ingested book exposes its TOC."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}/toc")
    assert response.status_code == 200
    payload = response.json()
    assert payload["book_urn"] == SAMPLE_BOOK_URN
    assert len(payload["entries"]) >= MIN_TOC_ENTRIES


def test_should_return_404_for_toc_of_unknown_urn(client: TestClient) -> None:
    """Unknown URN returns 404."""
    response = client.get("/api/books/no-such-book/toc")
    assert response.status_code == 404


def test_should_return_first_page_with_content(client: TestClient) -> None:
    """Page 1 of a real book serves its raw Arabic text; no parsed hadiths yet."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}/pages/{SAMPLE_FIRST_PAGE}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["page_number"] == SAMPLE_FIRST_PAGE
    assert payload["hadiths"] == []
    body = payload["text_ar"]
    assert len(body) >= MIN_PAGE_BODY_CHARS
    assert any("؀" <= c <= "ۿ" for c in body)


def test_should_serve_raw_text_not_a_fabricated_hadith(client: TestClient) -> None:
    """Pre-pipeline corpus pages carry raw text_ar, not a fabricated empty-isnad hadith."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}/pages/{SAMPLE_FIRST_PAGE}")
    payload = response.json()
    assert payload["hadiths"] == []
    assert payload["text_ar"] is not None
    assert len(payload["text_ar"]) >= MIN_PAGE_BODY_CHARS


def test_should_return_404_for_unknown_page(client: TestClient) -> None:
    """A page beyond the book returns 404."""
    response = client.get(f"/api/books/{SAMPLE_BOOK_URN}/pages/999999")
    assert response.status_code == 404


def test_should_scope_in_book_search_to_the_book(client: TestClient) -> None:
    """In-book search (the corpus engine scoped by URN) returns page+snippet
    hits confined to the book, fewer than the same query across the corpus."""
    in_book = client.get(f"/api/books/{SAMPLE_BOOK_URN}/search", params={"q": IN_BOOK_QUERY}).json()
    assert in_book["total"] >= 1
    item = in_book["items"][0]
    assert set(item.keys()) == {"page", "snippet"}
    assert item["page"] >= 1 and item["snippet"]
    corpus_wide = client.get("/api/search", params={"q": IN_BOOK_QUERY, "limit": 1}).json()
    assert in_book["total"] <= corpus_wide["total"]


def test_should_return_empty_in_book_search_when_query_blank(client: TestClient) -> None:
    """A blank in-book query yields no matches rather than the whole book."""
    payload = client.get(f"/api/books/{SAMPLE_BOOK_URN}/search", params={"q": ""}).json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_should_return_validated_page_rows_for_a_known_book() -> None:
    """page_rows — the one page accessor get_page + the index builder share —
    yields ordered (page, content) rows for a real book."""
    rows = reader_repo.page_rows(SAMPLE_BOOK_URN)
    assert rows
    assert rows[0].page >= 1
    assert rows[0].content


def test_should_raise_not_found_when_page_rows_for_unknown_book() -> None:
    """An unknown URN raises rather than returning an empty page list."""
    with pytest.raises(ResourceNotFoundError):
        reader_repo.page_rows("no-such-book")


def test_should_raise_when_source_content_is_malformed() -> None:
    """A present-but-malformed content section raises, not masquerade as empty."""
    with pytest.raises(reader_repo.ReaderSourceError):
        reader_repo._content_rows({"content": "not-an-object"})
    with pytest.raises(reader_repo.ReaderSourceError):
        reader_repo._content_rows({"content": {"1": "not-a-list"}})


def test_should_return_empty_rows_when_source_has_no_content() -> None:
    """An absent content section is a legitimately page-less book, yielding []."""
    assert reader_repo._content_rows({}) == []


def test_should_raise_when_source_maps_multiple_books() -> None:
    """A source file mapping more than one book is corruption, surfaced loudly."""
    with pytest.raises(reader_repo.ReaderSourceError):
        reader_repo._first_book_key({"1": [], "2": []})
