"""Tests for ``GET /api/person`` (paginated + filtered), detail, edges, events.

These run against the real ``data/registry.db`` artifact built by
``scripts/build_registry.py``, so the assertions use comfortable floors
rather than exact counts.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

PERSON_MIN_TOTAL = 100_000
SAMPLE_LIMIT = 5
KNOWN_ID = 22
UNKNOWN_ID = 99_999_999
SUFYAN = "سفيان"


def test_should_return_paginated_envelope_when_listing(client: TestClient) -> None:
    """`/api/person` returns {items, total, limit, offset}."""
    response = client.get("/api/person")
    assert response.status_code == 200
    assert set(response.json().keys()) == {"items", "total", "limit", "offset"}


def test_should_load_the_full_corpus(client: TestClient) -> None:
    """The artifact carries the whole person corpus; assert a comfortable floor."""
    assert client.get("/api/person").json()["total"] >= PERSON_MIN_TOTAL


def test_should_respect_limit_parameter(client: TestClient) -> None:
    """`?limit=N` caps items at N."""
    payload = client.get("/api/person", params={"limit": SAMPLE_LIMIT}).json()
    assert len(payload["items"]) == SAMPLE_LIMIT


def test_should_filter_by_tradition_when_given(client: TestClient) -> None:
    """`?tradition=shia` narrows every row to that tradition."""
    payload = client.get("/api/person", params={"tradition": "shia", "limit": SAMPLE_LIMIT}).json()
    assert payload["total"] >= 1
    assert all(item["tradition"] == "shia" for item in payload["items"])


def test_should_filter_to_evented_when_has_events(client: TestClient) -> None:
    """`?has_events=true` returns only persons carrying at least one event."""
    payload = client.get("/api/person", params={"has_events": "true", "limit": SAMPLE_LIMIT}).json()
    assert payload["total"] >= 1
    assert all(item["event_count"] > 0 for item in payload["items"])


def test_should_narrow_total_on_query_substring(client: TestClient) -> None:
    """A name substring query returns a strict, non-empty subset of the corpus."""
    base = client.get("/api/person").json()["total"]
    narrowed = client.get("/api/person", params={"q": SUFYAN}).json()["total"]
    assert 0 < narrowed < base


def test_should_return_detail_when_id_known(client: TestClient) -> None:
    """A known id returns that single enriched person with a reliability list."""
    response = client.get(f"/api/person/{KNOWN_ID}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["person_id"] == KNOWN_ID
    assert isinstance(payload["reliability"], list)


def test_should_return_edges_for_a_person(client: TestClient) -> None:
    """The edges sub-resource returns a list of teacher/student relations."""
    response = client.get(f"/api/person/{KNOWN_ID}/edges")
    assert response.status_code == 200
    edges = response.json()
    assert isinstance(edges, list)
    assert all("relation" in edge and "name" in edge for edge in edges)


def test_should_return_events_for_a_person(client: TestClient) -> None:
    """The events sub-resource returns a list (possibly empty) of events."""
    response = client.get(f"/api/person/{KNOWN_ID}/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_should_return_404_when_id_unknown(client: TestClient) -> None:
    """An out-of-range id yields a 404 naming the identifier."""
    response = client.get(f"/api/person/{UNKNOWN_ID}")
    assert response.status_code == 404
    assert str(UNKNOWN_ID) in response.json()["detail"]
