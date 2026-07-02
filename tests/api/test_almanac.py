"""Tests for ``GET /api/almanac``."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_should_return_the_almanac(client: TestClient) -> None:
    """The endpoint serves both tables, non-empty."""
    response = client.get("/api/almanac")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"observances", "events"}
    assert payload["observances"]
    assert payload["events"]


def test_should_carry_ashura_in_muharram(client: TestClient) -> None:
    """Sanity anchor: the almanac knows ʿĀshūrāʾ, 10 Muḥarram."""
    payload = client.get("/api/almanac").json()
    assert any(o["month"] == 1 and o["day"] == 10 for o in payload["observances"])
