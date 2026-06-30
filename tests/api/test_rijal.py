"""Tests for ``GET /api/rijal`` (paginated + filtered) and ``/api/rijal/{id}``.

These run against the real ``data/registry.db`` artifact built by
``scripts/build_registry.py``, so the assertions use comfortable floors
rather than exact counts.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

RIJAL_MIN_TOTAL = 200_000
SAMPLE_LIMIT = 5
KNOWN_ID = 0
UNKNOWN_ID = 99_999_999
SUFYAN = "سفيان"


def test_should_return_paginated_envelope_when_listing(client: TestClient) -> None:
    """`/api/rijal` returns {items, total, limit, offset}."""
    response = client.get("/api/rijal")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"items", "total", "limit", "offset"}


def test_should_load_the_full_corpus(client: TestClient) -> None:
    """The artifact carries the whole rijal corpus; assert a comfortable floor."""
    assert client.get("/api/rijal").json()["total"] >= RIJAL_MIN_TOTAL


def test_should_respect_limit_parameter(client: TestClient) -> None:
    """`?limit=N` caps items at N."""
    payload = client.get("/api/rijal", params={"limit": SAMPLE_LIMIT}).json()
    assert len(payload["items"]) == SAMPLE_LIMIT
    assert payload["limit"] == SAMPLE_LIMIT


def test_should_filter_by_tradition_when_given(client: TestClient) -> None:
    """`?tradition=sunni` narrows every row to that tradition."""
    payload = client.get("/api/rijal", params={"tradition": "sunni", "limit": SAMPLE_LIMIT}).json()
    assert payload["total"] >= 1
    assert all(item["tradition"] == "sunni" for item in payload["items"])


def test_should_filter_to_graded_when_has_reliability(client: TestClient) -> None:
    """`?has_reliability=true` returns only entries carrying a reliability term."""
    payload = client.get(
        "/api/rijal", params={"has_reliability": "true", "limit": SAMPLE_LIMIT}
    ).json()
    assert all(item["reliability_term"] for item in payload["items"])


def test_should_narrow_total_on_query_substring(client: TestClient) -> None:
    """A name substring query returns a strict, non-empty subset of the corpus."""
    base = client.get("/api/rijal").json()["total"]
    narrowed = client.get("/api/rijal", params={"q": SUFYAN}).json()["total"]
    assert 0 < narrowed < base


def test_should_return_detail_when_id_known(client: TestClient) -> None:
    """A known id returns that single rijal entry."""
    response = client.get(f"/api/rijal/{KNOWN_ID}")
    assert response.status_code == 200
    assert response.json()["id"] == KNOWN_ID


def test_should_return_404_when_id_unknown(client: TestClient) -> None:
    """An out-of-range id yields a 404 naming the identifier."""
    response = client.get(f"/api/rijal/{UNKNOWN_ID}")
    assert response.status_code == 404
    assert str(UNKNOWN_ID) in response.json()["detail"]
