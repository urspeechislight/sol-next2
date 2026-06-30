"""HTTP route: ``GET /api/domains`` — the IA taxonomy for the React cabinet."""

from __future__ import annotations

from fastapi import APIRouter

from backend.core.http import status
from backend.models.domain import Domain
from backend.repositories import domains as domains_repo

router = APIRouter(tags=["domains"])

router.add_api_route(
    "/domains",
    domains_repo.list_domains,
    methods=["GET"],
    response_model=list[Domain],
    status_code=status.HTTP_200_OK,
    summary="List all knowledge domains and their categories.",
)
