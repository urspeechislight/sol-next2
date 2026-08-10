"""HTTP routes for cross-corpus full-text search + facet lookups.

All routes register via ``add_api_route``. ``/search`` is the content search
(FTS5 over page text, ``exact``/``broad`` mode, filtered by category -> book ->
volume) -> ``Page[CorpusMatch]``. ``/search/facets`` returns the categories/
books/volumes that have matches. The paginated routes take the shared
``PageParams``. Catalog search lives on ``/works?q=`` (volume-folded works);
narrators are searched via the rijal route.

``SearchMode`` is a closed ``Literal`` set, so FastAPI rejects an unknown mode
with 422 rather than the repo silently defaulting it to ``exact``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageDep
from backend.api._routes import as_page, get_route
from backend.api._validation import reject_unknown
from backend.models.pagination import Page
from backend.models.search import CorpusMatch, SearchFacets, SearchMode
from backend.repositories import _taxonomy
from backend.repositories import corpus as corpus_repo

router = APIRouter(tags=["search"])

_MODE_DESC = "Match mode: 'exact' (whole phrase) or 'broad' (sub-phrases)."


_CATEGORY_DESC = "Restrict to these category slugs (repeatable; values OR together)."


def _checked_categories(category: list[str] | None) -> tuple[str, ...]:
    """Validate every repeated ``category`` value against the taxonomy (422 on
    an unknown slug) and freeze the set for the repo query. ``None`` is the
    absent-param default and means no category constraint."""
    if category is None:
        return ()
    for slug in category:
        reject_unknown("category", slug, _taxonomy.is_known_category)
    return tuple(category)


class SearchParams:
    """Corpus content-search query + scope filters as request parameters."""

    def __init__(
        self,
        q: str = Query(default="", description="Arabic phrase; folded before matching."),
        mode: Annotated[SearchMode, Query(description=_MODE_DESC)] = "exact",
        category: Annotated[list[str] | None, Query(description=_CATEGORY_DESC)] = None,
        book: str = Query(default="", description="Restrict to a book title (a work)."),
        volume: int = Query(default=0, ge=0, description="Restrict to a volume number (0 = any)."),
    ) -> None:
        self.query = corpus_repo.SearchQuery(
            q=q, mode=mode, categories=_checked_categories(category), book=book, volume=volume
        )


async def _search(
    page: PageDep,
    params: Annotated[SearchParams, Depends()],
) -> Page[CorpusMatch]:
    """Wrap the repo's (slice, total) into a Page[CorpusMatch] envelope."""
    return as_page(
        Page[CorpusMatch],
        page,
        await corpus_repo.search(params.query, limit=page.limit, offset=page.offset),
    )


async def _search_facets(
    q: str = Query(default="", description="Arabic phrase; folded before matching."),
    mode: Annotated[SearchMode, Query(description=_MODE_DESC)] = "exact",
    category: Annotated[list[str] | None, Query(description=_CATEGORY_DESC)] = None,
    book: str = Query(default="", description="Book to scope volume facets to."),
) -> SearchFacets:
    """Return the categories, books, and volumes that hold matches for ``q``."""
    return await corpus_repo.facets(
        q=q, mode=mode, categories=_checked_categories(category), book=book
    )


get_route(
    router,
    "/search",
    _search,
    response_model=Page[CorpusMatch],
    summary="Full-text search across all book content (diacritic-insensitive).",
)
get_route(
    router,
    "/search/facets",
    _search_facets,
    response_model=SearchFacets,
    summary="Category -> book -> volume filters available for a search query.",
)
