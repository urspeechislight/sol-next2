"""HTTP routes for the rijal registry: paginated list + detail.

Both routes register via ``add_api_route``. The list handler filters + wraps the
repo's ``(slice, total)`` into a ``Page[RijalEntry]`` envelope and takes the
shared ``PageParams``; the detail route binds ``registry.get_rijal`` directly.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageDep
from backend.api._routes import as_page, get_route
from backend.models.narrator import RijalEntry
from backend.models.pagination import Page
from backend.repositories import registry

router = APIRouter(tags=["rijal"])


class RijalFilterParams:
    """Rijal listing filters as request query parameters."""

    def __init__(
        self,
        q: str = Query(default="", description="Substring match on name / kunya / nisba."),
        tradition: str = Query(
            default="", description="Filter by tradition (sunni / shia / both)."
        ),
        category: str = Query(default="", description="Filter by data-quality category."),
        has_teachers: bool = Query(
            default=False, description="Only entries with at least one teacher."
        ),
        has_reliability: bool = Query(
            default=False, description="Only entries carrying a reliability term."
        ),
    ) -> None:
        self.filter = registry.RijalFilter(
            q=q,
            tradition=tradition,
            category=category,
            has_teachers=has_teachers,
            has_reliability=has_reliability,
        )


async def _list_rijal(
    page: PageDep,
    filters: Annotated[RijalFilterParams, Depends()],
) -> Page[RijalEntry]:
    """Wrap the repo's (slice, total) into a Page[RijalEntry] envelope."""
    return as_page(
        Page[RijalEntry],
        page,
        registry.list_rijal(filters.filter, limit=page.limit, offset=page.offset),
    )


get_route(
    router,
    "/rijal",
    _list_rijal,
    response_model=Page[RijalEntry],
    summary="List rijal narrators with pagination + filters.",
)
get_route(
    router,
    "/rijal/{entry_id}",
    registry.get_rijal,
    response_model=RijalEntry,
    summary="Get a single rijal entry by id.",
)
