"""HTTP route: ``GET /api/almanac`` — Hijri observances + chronicle events."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api._routes import get_route
from backend.models.almanac import Almanac
from backend.repositories import almanac as almanac_repo

router = APIRouter(tags=["almanac"])

get_route(
    router,
    "/almanac",
    almanac_repo.get_almanac,
    response_model=Almanac,
    summary="The Hijri almanac: observances and chronicle events.",
)
