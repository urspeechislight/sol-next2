"""HTTP routes for the rijal registry: paginated list + detail.

Both routes register via ``add_api_route``. The list handler filters + wraps the
repo's ``(slice, total)`` into a ``Page[RijalEntry]`` envelope and takes the
shared ``PageParams``; the detail route binds ``registry.get_rijal`` directly.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageParams
from backend.core.http import status
from backend.models.narrator import RijalEntry
from backend.models.pagination import Page
from backend.repositories import registry

router = APIRouter(tags=["rijal"])


async def _list_rijal(
    page: Annotated[PageParams, Depends()],
    q: str = Query(default="", description="Substring match on name / kunya / nisba."),
    tradition: str = Query(default="", description="Filter by tradition (sunni / shia / both)."),
    category: str = Query(default="", description="Filter by data-quality category."),
    has_teachers: bool = Query(
        default=False, description="Only entries with at least one teacher."
    ),
    has_reliability: bool = Query(
        default=False, description="Only entries carrying a reliability term."
    ),
) -> Page[RijalEntry]:
    """Wrap the repo's (slice, total) into a Page[RijalEntry] envelope."""
    items, total = registry.list_rijal(
        q=q,
        tradition=tradition,
        category=category,
        has_teachers=has_teachers,
        has_reliability=has_reliability,
        limit=page.limit,
        offset=page.offset,
    )
    return Page[RijalEntry](items=items, total=total, limit=page.limit, offset=page.offset)


router.add_api_route(
    "/rijal",
    _list_rijal,
    methods=["GET"],
    response_model=Page[RijalEntry],
    status_code=status.HTTP_200_OK,
    summary="List rijal narrators with pagination + filters.",
)
router.add_api_route(
    "/rijal/{entry_id}",
    registry.get_rijal,
    methods=["GET"],
    response_model=RijalEntry,
    status_code=status.HTTP_200_OK,
    summary="Get a single rijal entry by id.",
)
