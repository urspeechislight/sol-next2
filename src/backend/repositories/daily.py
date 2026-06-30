"""Repository for the Daily editorial — loads from ``data/daily.json``."""

from __future__ import annotations

from backend.models.daily import Daily
from backend.repositories._data_loader import load_json


def get_today() -> Daily:
    """Return today's curated Daily payload."""
    return Daily.model_validate(load_json("daily.json"))
