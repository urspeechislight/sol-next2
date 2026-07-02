"""HTTP route: ``GET /api/works``: the volume-folded Library listing.

One row per work (not per volume), scoped by category, domain, or tradition.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from backend.api._pagination import PageDep
from backend.api._routes import as_page, get_route
from backend.core.http import status
from backend.models.book import Canonical
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown {param}: {value!r}.",
        )


async def _list_works(
    page: PageDep,
    category: str | None = Query(default=None, description="Filter by category slug."),
    domain: str | None = Query(default=None, description="Filter by domain id."),
    tradition: str | None = Query(default=None, description="Tradition: sunni, shia, or shared."),
    canonical: Annotated[Canonical | None, Query(description="Filter to a canonical rank.")] = None,
    q: str = Query(default="", description="Search works by title or author."),
) -> Page[Work]:
    """Wrap the repo's (slice, total) of works into a Page[Work] envelope."""
    _reject_unknown("domain", domain, _taxonomy.is_known_domain)
    _reject_unknown("category", category, _taxonomy.is_known_category)
    _reject_unknown("tradition", tradition, _taxonomy.is_known_tradition)
    return as_page(
        Page[Work],
        page,
        books_repo.list_works(
            books_repo.WorksQuery(
                category=category, domain=domain, tradition=tradition, canonical=canonical, q=q
            ),
            limit=page.limit,
            offset=page.offset,
        ),
    )


get_route(
    router,
    "/works",
    _list_works,
    response_model=Page[Work],
    summary="List volume-folded works, optionally filtered by category, domain, or tradition.",
)
