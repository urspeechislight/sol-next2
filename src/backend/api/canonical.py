"""HTTP routes for canonical narrator profiles: paginated list + detail.

Both routes register via ``add_api_route``. The list handler filters + wraps the
repo's ``(slice, total)`` into a ``Page`` envelope and takes the shared
``PageParams``; the detail route binds ``registry.get_canonical`` directly.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.api._pagination import PageDep
from backend.api._routes import as_page, get_route
from backend.models.narrator import CanonicalEntry
from backend.models.pagination import Page
from backend.repositories import registry

router = APIRouter(tags=["canonical"])


async def _list_canonical(
    page: PageDep,
    q: str = Query(default="", description="Substring match on name / kunya / nisba."),
    merged_only: bool = Query(
        default=False, description="Only profiles merged from more than one raw entry."
    ),
) -> Page[CanonicalEntry]:
    """Wrap the repo's (slice, total) into a Page[CanonicalEntry] envelope."""
    return as_page(
        Page[CanonicalEntry],
        page,
        registry.list_canonical(q=q, merged_only=merged_only, limit=page.limit, offset=page.offset),
    )


get_route(
    router,
    "/canonical",
    _list_canonical,
    response_model=Page[CanonicalEntry],
    summary="List canonical narrator profiles with pagination + filters.",
)
get_route(
    router,
    "/canonical/{canonical_id}",
    registry.get_canonical,
    response_model=CanonicalEntry,
    summary="Get a single canonical profile by id.",
)
