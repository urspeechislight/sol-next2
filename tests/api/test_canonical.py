"""Tests for ``GET /api/canonical`` (paginated + filtered) and detail.

These run against the real ``data/registry.db`` artifact, so the assertions
use comfortable floors rather than exact counts.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

CANONICAL_MIN_TOTAL = 100_000
SAMPLE_LIMIT = 5
KNOWN_ID = 1
UNKNOWN_ID = 99_999_999


def test_should_return_paginated_envelope_when_listing(client: TestClient) -> None:
    """`/api/canonical` returns {items, total, limit, offset}."""
    response = client.get("/api/canonical")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"items", "total", "limit", "offset"}


def test_should_load_the_full_corpus(client: TestClient) -> None:
    """The artifact carries the whole canonical corpus; assert a floor."""
    assert client.get("/api/canonical").json()["total"] >= CANONICAL_MIN_TOTAL


def test_should_respect_limit_parameter(client: TestClient) -> None:
    """`?limit=N` caps items at N."""
    payload = client.get("/api/canonical", params={"limit": SAMPLE_LIMIT}).json()
    assert len(payload["items"]) == SAMPLE_LIMIT
    assert payload["limit"] == SAMPLE_LIMIT


def test_should_return_only_merged_when_merged_only(client: TestClient) -> None:
    """`?merged_only=true` keeps only profiles fused from >1 raw entry."""
    payload = client.get(
        "/api/canonical", params={"merged_only": "true", "limit": SAMPLE_LIMIT}
    ).json()
    assert payload["total"] >= 1
    assert all(item["entry_count"] > 1 for item in payload["items"])


def test_should_return_detail_when_id_known(client: TestClient) -> None:
    """A known canonical id returns that single profile."""
    response = client.get(f"/api/canonical/{KNOWN_ID}")
    assert response.status_code == 200
    assert response.json()["canonical_id"] == KNOWN_ID


def test_should_return_404_when_id_unknown(client: TestClient) -> None:
    """An out-of-range id yields a 404 naming the identifier."""
    response = client.get(f"/api/canonical/{UNKNOWN_ID}")
    assert response.status_code == 404
    assert str(UNKNOWN_ID) in response.json()["detail"]
