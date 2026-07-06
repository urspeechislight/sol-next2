"""Tests for ``GET /api/daily`` and the date rotation behind it."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.repositories import daily as daily_repo

EXPECTED_TAFSIR_COUNT = 2
EXPECTED_BOOK_POOL = 7


def test_should_return_daily_payload(client: TestClient) -> None:
    """The endpoint returns the full Daily envelope."""
    response = client.get("/api/daily")
    assert response.status_code == 200
    assert set(response.json().keys()) == {"verse", "hadith", "book"}


def test_should_include_two_tafsirs_for_the_verse(client: TestClient) -> None:
    """The verse carries one Sunni and one Imami tafsir excerpt."""
    payload = client.get("/api/daily").json()
    assert len(payload["verse"]["tafsirs"]) == EXPECTED_TAFSIR_COUNT


def test_should_match_the_quran_text_for_the_verse(client: TestClient) -> None:
    """The served ayah is byte-identical to the Qurʾān endpoint's text.

    The daily verse is composed from the same artifact the reader serves; any
    drift between the two would put two different claims of scripture on the
    same site.
    """
    verse = client.get("/api/daily").json()["verse"]
    canonical = client.get(f"/api/quran/{verse['surah_n']}/{verse['ayah_n']}").json()
    assert canonical["text_ar"] == verse["ayah_ar"]


def test_should_only_cite_urns_the_catalog_serves(client: TestClient) -> None:
    """Every non-null deep link in the payload resolves to a served book.

    Regression for the fixture-era payload whose URNs (``KafSlm32``,
    ``BukhJam2``, ...) were fabricated identifiers that 404'd in the reader.
    A citation without a held work must carry ``urn: null``, never a guess.
    """
    payload = client.get("/api/daily").json()
    urns: list[str | None] = [t["urn"] for t in payload["verse"]["tafsirs"]]
    urns.append(payload["hadith"]["source"]["urn"])
    urns.extend(p["urn"] for p in payload["hadith"]["parallels"])
    urns.append(payload["book"]["urn"])
    for urn in urns:
        if urn is None:
            continue
        assert client.get(f"/api/books/{urn}").status_code == 200, urn


def test_should_rotate_the_book_pick_daily_and_deterministically() -> None:
    """Consecutive days walk the whole book pool; the same day always agrees."""
    start = date(2026, 7, 1)
    picks = [
        daily_repo.for_day(start + timedelta(days=i)).book.urn for i in range(EXPECTED_BOOK_POOL)
    ]
    assert len(set(picks)) == EXPECTED_BOOK_POOL
    assert daily_repo.for_day(start).book.urn == picks[0]


def test_should_anchor_the_book_pick_inside_the_book(client: TestClient) -> None:
    """Every pool book's ``open_to`` page exists in the book it points at."""
    start = date(2026, 7, 1)
    for i in range(EXPECTED_BOOK_POOL):
        pick = daily_repo.for_day(start + timedelta(days=i)).book
        book = client.get(f"/api/books/{pick.urn}").json()
        page_count = book["page_count"]
        assert page_count is None or pick.open_to.page <= page_count, pick.urn
