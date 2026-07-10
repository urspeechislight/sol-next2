"""Tests for the aggregate /api/health probe."""

from __future__ import annotations

from fastapi.testclient import TestClient

_EXPECTED = {"domains", "books", "rijal", "person", "quran", "daily", "almanac", "citations"}


def test_should_probe_every_subsystem_and_return_200(client: TestClient) -> None:
    """The probe answers 200 and covers each major subsystem."""
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert _EXPECTED.issubset({check["name"] for check in body["checks"]})


def test_should_shape_each_check_with_a_name_flag_error(client: TestClient) -> None:
    """Each check names its subsystem, carries an ok flag, and an error string."""
    for check in client.get("/api/health").json()["checks"]:
        assert isinstance(check["name"], str) and check["name"]
        assert isinstance(check["ok"], bool)
        assert isinstance(check["error"], str)
