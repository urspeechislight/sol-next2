"""HTTP routes for canonical narrator profiles: paginated list + detail.

Both routes register via ``add_api_route``. The list handler filters + wraps the
repo's ``(slice, total)`` into a ``Page`` envelope and takes the shared
``PageParams``; the detail route binds ``registry.get_canonical`` directly.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageParams
from backend.core.http import status
from backend.models.narrator import CanonicalEntry
from backend.models.pagination import Page
from backend.repositories import registry

router = APIRouter(tags=["canonical"])


async def _list_canonical(
    page: Annotated[PageParams, Depends()],
    q: str = Query(default="", description="Substring match on name / kunya / nisba."),
    merged_only: bool = Query(
        default=False, description="Only profiles merged from more than one raw entry."
    ),
) -> Page[CanonicalEntry]:
    """Wrap the repo's (slice, total) into a Page[CanonicalEntry] envelope."""
    items, total = registry.list_canonical(
        q=q, merged_only=merged_only, limit=page.limit, offset=page.offset
    )
    return Page[CanonicalEntry](items=items, total=total, limit=page.limit, offset=page.offset)


router.add_api_route(
    "/canonical",
    _list_canonical,
    methods=["GET"],
    response_model=Page[CanonicalEntry],
    status_code=status.HTTP_200_OK,
    summary="List canonical narrator profiles with pagination + filters.",
)
router.add_api_route(
    "/canonical/{canonical_id}",
    registry.get_canonical,
    methods=["GET"],
    response_model=CanonicalEntry,
    status_code=status.HTTP_200_OK,
    summary="Get a single canonical profile by id.",
)
