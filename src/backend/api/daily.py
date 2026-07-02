"""HTTP route: ``GET /api/daily`` — curated editorial picks for today."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api._routes import get_route
from backend.models.daily import Daily
from backend.repositories import daily as daily_repo

router = APIRouter(tags=["daily"])

get_route(
    router,
    "/daily",
    daily_repo.get_today,
    response_model=Daily,
    summary="Today's verse, hadith, and book pick.",
)
