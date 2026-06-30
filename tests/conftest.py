"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """Reusable TestClient bound to the FastAPI app under test."""
    with TestClient(app) as test_client:
        yield test_client
