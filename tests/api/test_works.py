"""Tests for ``GET /api/works`` (the volume-folded Library listing) + its input
validation: an unknown ``?domain=`` is a 400, not a silently-empty 200.
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


def test_should_reject_an_unknown_domain_with_400(client: TestClient) -> None:
    """An unknown ?domain= is a client error, never a silent empty list."""
    response = client.get("/api/works", params={"domain": "definitely-not-a-domain"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_should_accept_a_known_domain_when_filtering(client: TestClient) -> None:
    """A real domain id from the taxonomy filters the listing without error."""
    known = _taxonomy.DOMAINS[0].id
    response = client.get("/api/works", params={"domain": known})
    assert response.status_code == status.HTTP_200_OK
