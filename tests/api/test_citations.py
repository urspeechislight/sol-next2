"""Tests for the citation sidecar routes: per-page links + reverse concordance."""

from __future__ import annotations

from fastapi.testclient import TestClient

LINKABLE = {"exact", "short", "neighbor"}
FIXTURE_URN = "J0sPYclO_01"
FIXTURE_PAGE = 376
AYAT_AL_KURSI_SURAH = 2
AYAT_AL_KURSI_AYA = 255


def test_should_return_verified_citations_for_a_page(client: TestClient) -> None:
    """A page rich in Qur'an references returns its located citations."""
    response = client.get(f"/api/books/{FIXTURE_URN}/pages/{FIXTURE_PAGE}/citations")
    assert response.status_code == 200
    body = response.json()
    assert len(body) > 1
    first = body[0]
    assert set(first) == {"offset", "length", "surah", "aya_start", "aya_end", "verse_match"}
    assert 1 <= first["surah"] <= 114
    assert first["aya_start"] >= 1


def test_should_order_citations_by_position_in_the_page(client: TestClient) -> None:
    """Citations arrive in reading order so the reader can anchor them in place."""
    body = client.get(f"/api/books/{FIXTURE_URN}/pages/{FIXTURE_PAGE}/citations").json()
    offsets = [c["offset"] for c in body]
    assert offsets == sorted(offsets)


def test_should_only_serve_linkable_match_verdicts(client: TestClient) -> None:
    """Only verse-verified citations are served; the review tail is withheld."""
    body = client.get(f"/api/books/{FIXTURE_URN}/pages/{FIXTURE_PAGE}/citations").json()
    assert all(c["verse_match"] in LINKABLE for c in body)


def test_should_return_empty_list_for_unknown_urn(client: TestClient) -> None:
    """An unknown book yields an empty apparatus, not an error."""
    response = client.get("/api/books/no-such-book/pages/1/citations")
    assert response.status_code == 200
    assert response.json() == []


def test_should_count_books_citing_ayat_al_kursi(client: TestClient) -> None:
    """Reverse concordance returns how many distinct books cite a verse."""
    response = client.get(f"/api/citations/{AYAT_AL_KURSI_SURAH}/{AYAT_AL_KURSI_AYA}/books")
    assert response.status_code == 200
    assert response.json()["books"] >= 1
