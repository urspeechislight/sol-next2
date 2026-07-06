"""Repository for the Hijri almanac — loads ``data/almanac.json``."""

from __future__ import annotations

from backend.models.almanac import Almanac
from backend.repositories._data_loader import load_json


def get_almanac() -> Almanac:
    """Return the full almanac; the client selects for its own "today"."""
    return Almanac.model_validate(load_json("almanac.json"))
