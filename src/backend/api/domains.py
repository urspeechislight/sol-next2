"""HTTP route: ``GET /api/domains`` — the IA taxonomy for the React cabinet."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api._routes import get_route
from backend.models.domain import Domain
from backend.repositories import domains as domains_repo

router = APIRouter(tags=["domains"])

get_route(
    router,
    "/domains",
    domains_repo.list_domains,
    response_model=list[Domain],
    summary="List all knowledge domains and their categories.",
)
