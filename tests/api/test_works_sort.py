"""Tests for ``GET /api/works?sort=``: the closed set of orderings."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.core.http import status

SAMPLE = 120


def test_should_sort_dated_works_ascending_with_undated_last(client: TestClient) -> None:
    """?sort=death_year_ah orders the dated block ascending; undated follows it."""
    payload = client.get("/api/works", params={"sort": "death_year_ah", "limit": SAMPLE}).json()
    years = [w["death_year_ah"] for w in payload["items"]]
    dated = [y for y in years if y is not None]
    assert dated == sorted(dated)
    first_none = years.index(None) if None in years else len(years)
    assert all(y is None for y in years[first_none:])


def test_should_sort_deepest_works_first_by_volume_count(client: TestClient) -> None:
    """?sort=volume_count leads with the largest works, descending."""
    payload = client.get("/api/works", params={"sort": "volume_count", "limit": SAMPLE}).json()
    counts = [w["volume_count"] for w in payload["items"]]
    assert counts == sorted(counts, reverse=True)
    assert counts[0] > 1


def test_should_sort_ranked_tiers_first_then_death_year(client: TestClient) -> None:
    """?sort=canonical leads with the most authoritative editorial tier and
    orders each tier by death year ascending (undated last within the tier)."""
    tier_order = ["primary_reference", "primary", "secondary", "tertiary", None]
    payload = client.get("/api/works", params={"sort": "canonical", "limit": SAMPLE}).json()
    keys = [
        (tier_order.index(w["canonical"]), w["death_year_ah"] is None, w["death_year_ah"] or 0)
        for w in payload["items"]
    ]
    assert keys == sorted(keys)
    assert payload["items"][0]["canonical"] == "primary_reference"


def test_should_reject_an_unknown_sort_with_422(client: TestClient) -> None:
    """An unknown ?sort= is a client error, never a silently unsorted 200.

    Regression: the parameter used to be absent, so ?sort=death_year_ah
    returned HTTP 200 in arbitrary storage order.
    """
    response = client.get("/api/works", params={"sort": "popularity"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
