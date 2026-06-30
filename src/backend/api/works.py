"""HTTP route: ``GET /api/works``: the volume-folded Library listing.

One row per work (not per volume), scoped by category, domain, or tradition.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api._pagination import PageParams
from backend.core.http import status
from backend.models.pagination import Page
from backend.models.work import Work
from backend.repositories import _taxonomy
from backend.repositories import books as books_repo

router = APIRouter(tags=["works"])


def _reject_unknown(param: str, value: str | None, predicate: Callable[[str], bool]) -> None:
    """Reject an unknown closed-set query value with 422 — the FastAPI validation-
    error convention shared with the Literal mode/field params — instead of letting
    it silently filter to an empty list. No-op when the value is absent (None)."""
    if value is not None and not predicate(value):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown {param}: {value!r}.",
        )


async def _list_works(
    page: Annotated[PageParams, Depends()],
    category: str | None = Query(default=None, description="Filter by category slug."),
    domain: str | None = Query(default=None, description="Filter by domain id."),
    tradition: str | None = Query(default=None, description="Tradition: sunni, shia, or shared."),
    q: str = Query(default="", description="Search works by title or author."),
) -> Page[Work]:
    """Wrap the repo's (slice, total) of works into a Page[Work] envelope."""
    _reject_unknown("domain", domain, _taxonomy.is_known_domain)
    _reject_unknown("category", category, _taxonomy.is_known_category)
    _reject_unknown("tradition", tradition, _taxonomy.is_known_tradition)
    items, total = books_repo.list_works(
        category=category,
        domain=domain,
        tradition=tradition,
        q=q,
        limit=page.limit,
        offset=page.offset,
    )
    return Page[Work](items=items, total=total, limit=page.limit, offset=page.offset)


router.add_api_route(
    "/works",
    _list_works,
    methods=["GET"],
    response_model=Page[Work],
    status_code=status.HTTP_200_OK,
    summary="List volume-folded works, optionally filtered by category, domain, or tradition.",
)
