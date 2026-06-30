"""Tests for ``GET /api/daily``."""

from __future__ import annotations

from fastapi.testclient import TestClient

EXPECTED_TAFSIR_COUNT = 2
EXPECTED_PARALLEL_COUNT = 2
EXPECTED_ROTATION_COUNT = 8


def test_should_return_daily_payload(client: TestClient) -> None:
    """The endpoint returns the full Daily envelope."""
    response = client.get("/api/daily")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"date", "verse", "hadith", "book", "rotation"}


def test_should_include_two_tafsirs_for_the_verse(client: TestClient) -> None:
    """The verse carries one Sunni and one Imami tafsir excerpt."""
    payload = client.get("/api/daily").json()
    assert len(payload["verse"]["tafsirs"]) == EXPECTED_TAFSIR_COUNT


def test_should_include_parallels_for_the_hadith(client: TestClient) -> None:
    """The hadith of the day surfaces parallels in other collections."""
    payload = client.get("/api/daily").json()
    assert len(payload["hadith"]["parallels"]) == EXPECTED_PARALLEL_COUNT


def test_should_include_rotation_of_urns(client: TestClient) -> None:
    """The rotation carousel ships 8 book URNs."""
    payload = client.get("/api/daily").json()
    assert len(payload["rotation"]) == EXPECTED_ROTATION_COUNT


def test_should_serialize_arabic_verse_text(client: TestClient) -> None:
    """Arabic ayah text round-trips correctly."""
    payload = client.get("/api/daily").json()
    assert "خَلَقَ" in payload["verse"]["ayah_ar"]
