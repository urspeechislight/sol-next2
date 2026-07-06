"""Tests for ``GET /api/works`` (the volume-folded Library listing) + its input
validation: an unknown ``?domain=`` is a 422, not a silently-empty 200.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.core.http import status
from backend.repositories import _taxonomy


def test_should_return_the_paginated_envelope_when_listing_works(client: TestClient) -> None:
    """`/api/works` returns {items, total, limit, offset} with works present."""
    response = client.get("/api/works")
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert set(payload.keys()) == {"items", "total", "limit", "offset"}
    assert payload["total"] > 0


def test_should_reject_an_unknown_domain_with_422(client: TestClient) -> None:
    """An unknown ?domain= is a client error, never a silent empty list."""
    response = client.get("/api/works", params={"domain": "definitely-not-a-domain"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_should_reject_an_unknown_category_with_422(client: TestClient) -> None:
    """An unknown ?category= is a client error, exactly like an unknown domain."""
    response = client.get("/api/works", params={"category": "definitely-not-a-category"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_should_reject_an_unknown_tradition_with_422(client: TestClient) -> None:
    """An unknown ?tradition= is a client error, exactly like an unknown domain."""
    response = client.get("/api/works", params={"tradition": "definitely-not-a-tradition"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_should_accept_a_known_domain_when_filtering(client: TestClient) -> None:
    """A real domain id from the taxonomy filters the listing without error."""
    known = _taxonomy.DOMAINS[0].id
    response = client.get("/api/works", params={"domain": known})
    assert response.status_code == status.HTTP_200_OK


def test_should_filter_to_landmark_works_when_canonical_given(client: TestClient) -> None:
    """?canonical=primary_reference returns only that rank; the shelf never mixes."""
    payload = client.get(
        "/api/works", params={"canonical": "primary_reference", "limit": 50}
    ).json()
    assert payload["total"] > 0
    assert all(w["canonical"] == "primary_reference" for w in payload["items"])


def test_should_reject_an_unknown_canonical_rank_with_422(client: TestClient) -> None:
    """An unknown ?canonical= is a client error like the other closed sets."""
    response = client.get("/api/works", params={"canonical": "not-a-rank"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_should_resolve_to_the_one_work_containing_a_given_urn(client: TestClient) -> None:
    """?urn=<volume urn> narrows to exactly the work that volume folds into."""
    payload = client.get("/api/works", params={"urn": "sY-50TSO"}).json()
    assert payload["total"] == 1
    assert "sY-50TSO" in payload["items"][0]["volumes"]


def test_should_union_repeated_urn_params_across_different_works(client: TestClient) -> None:
    """Two volumes from different works both come back; repeated ?urn= values OR
    together exactly like the corpus search's repeated ?category=."""
    other = next(
        w["first_urn"]
        for w in client.get("/api/works", params={"limit": 5}).json()["items"]
        if w["stem"] != "sY-50TSO"
    )
    payload = client.get("/api/works", params={"urn": ["sY-50TSO", other]}).json()
    assert payload["total"] == 2


def test_should_return_empty_when_urn_matches_no_work(client: TestClient) -> None:
    """An unrecognized urn is not user-typed taxonomy input: it resolves to zero
    matches rather than a 422, since a content-search hit's urn is always real."""
    payload = client.get("/api/works", params={"urn": "definitely-not-a-real-urn"}).json()
    assert payload["total"] == 0
