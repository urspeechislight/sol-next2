"""HTTP route: ``GET /api/works``: the volume-folded Library listing.

One row per work (not per volume), scoped by category, domain, or tradition.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from backend.api._pagination import PageDep
from backend.api._routes import as_page, get_route
from backend.api._validation import reject_unknown
from backend.models.book import Canonical
from backend.models.pagination import Page
from backend.models.work import Work
from backend.repositories import _taxonomy
from backend.repositories import books as books_repo
from backend.repositories.books import WorkSort

router = APIRouter(tags=["works"])


async def _list_works(
    page: PageDep,
    category: str | None = Query(default=None, description="Filter by category slug."),
    domain: str | None = Query(default=None, description="Filter by domain id."),
    tradition: str | None = Query(default=None, description="Tradition: sunni, shia, or shared."),
    canonical: Annotated[Canonical | None, Query(description="Filter to a canonical rank.")] = None,
    q: str = Query(default="", description="Search works by title or author."),
    sort: Annotated[
        WorkSort | None,
        Query(
            description=(
                "Ordering: canonical (rank tier, then death year), "
                "death_year_ah (undated last), title_ar, or volume_count."
            )
        ),
    ] = None,
) -> Page[Work]:
    """Wrap the repo's (slice, total) of works into a Page[Work] envelope."""
    reject_unknown("domain", domain, _taxonomy.is_known_domain)
    reject_unknown("category", category, _taxonomy.is_known_category)
    reject_unknown("tradition", tradition, _taxonomy.is_known_tradition)
    return as_page(
        Page[Work],
        page,
        books_repo.list_works(
            books_repo.WorksQuery(
                category=category,
                domain=domain,
                tradition=tradition,
                canonical=canonical,
                q=q,
                sort=sort,
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
