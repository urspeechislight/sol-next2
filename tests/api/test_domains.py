"""Tests for ``GET /api/domains``."""

from __future__ import annotations

from fastapi.testclient import TestClient

EXPECTED_DOMAIN_COUNT = 8
EXPECTED_HADITH_CATEGORY_COUNT = 8


def test_should_return_seven_domains_when_listing(client: TestClient) -> None:
    """The taxonomy ships with exactly eight top-level domains."""
    response = client.get("/api/domains")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == EXPECTED_DOMAIN_COUNT


def test_should_include_hadith_domain_when_listing(client: TestClient) -> None:
    """The first domain is Hadith with eight categories."""
    response = client.get("/api/domains")
    payload = response.json()
    hadith = next(d for d in payload if d["id"] == "hadith")
    assert hadith["label"] == "Hadith"
    assert hadith["label_ar"] == "الحديث"
    assert len(hadith["categories"]) == EXPECTED_HADITH_CATEGORY_COUNT


def test_should_expose_arabic_labels_for_every_category(client: TestClient) -> None:
    """Every category carries a non-empty Arabic label."""
    response = client.get("/api/domains")
    for domain in response.json():
        for cat in domain["categories"]:
            assert cat["label_ar"], f"missing Arabic label on {cat['slug']}"


def test_should_set_cors_headers_for_frontend_origin(client: TestClient) -> None:
    """The static frontend on :8765 must be allowed via CORS."""
    response = client.get(
        "/api/domains",
        headers={"Origin": "http://127.0.0.1:8765"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:8765"


def test_should_return_ok_for_health_probe(client: TestClient) -> None:
    """`/health` returns 200 and a status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
