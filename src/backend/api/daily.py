"""HTTP route: ``GET /api/daily`` — curated editorial picks for today."""

from __future__ import annotations

from fastapi import APIRouter

from backend.core.http import status
from backend.models.daily import Daily
from backend.repositories import daily as daily_repo

router = APIRouter(tags=["daily"])

router.add_api_route(
    "/daily",
    daily_repo.get_today,
    methods=["GET"],
    response_model=Daily,
    status_code=status.HTTP_200_OK,
    summary="Today's verse, hadith, and book pick.",
)
