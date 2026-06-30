"""HTTP routes for cross-corpus full-text search + book/facet lookups.

All routes register via ``add_api_route``. ``/search`` is the content search
(FTS5 over page text, ``exact``/``broad`` mode, filtered by category -> book ->
volume) -> ``Page[CorpusMatch]``. ``/search/facets`` returns the categories/
books/volumes that have matches. ``/search/books`` searches book metadata by
title / author -> ``Page[Book]``. The paginated routes take the shared
``PageParams``; narrators are searched via the rijal route.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageParams
from backend.core.http import status
from backend.models.book import Book
from backend.models.pagination import Page
from backend.models.search import CorpusMatch, SearchFacets
from backend.repositories import books as books_repo
from backend.repositories import corpus as corpus_repo

router = APIRouter(tags=["search"])

# Closed sets the query params accept; FastAPI rejects anything else with 422
# rather than the repo silently defaulting an unknown mode/field to exact/any.
SearchMode = Literal["exact", "broad"]
SearchField = Literal["title", "author", "any"]

_MODE_DESC = "Match mode: 'exact' (whole phrase) or 'broad' (sub-phrases)."


async def _search(
    page: Annotated[PageParams, Depends()],
    q: str = Query(default="", description="Arabic phrase; folded before matching."),
    mode: Annotated[SearchMode, Query(description=_MODE_DESC)] = "exact",
    category: str = Query(default="", description="Restrict to a category slug."),
    book: str = Query(default="", description="Restrict to a book title (a work)."),
    volume: int = Query(default=0, ge=0, description="Restrict to a volume number (0 = any)."),
) -> Page[CorpusMatch]:
    """Wrap the repo's (slice, total) into a Page[CorpusMatch] envelope."""
    items, total = corpus_repo.search(
        q=q,
        mode=mode,
        category=category,
        book=book,
        volume=volume,
        limit=page.limit,
        offset=page.offset,
    )
    return Page[CorpusMatch](items=items, total=total, limit=page.limit, offset=page.offset)


async def _search_facets(
    q: str = Query(default="", description="Arabic phrase; folded before matching."),
    mode: Annotated[SearchMode, Query(description=_MODE_DESC)] = "exact",
    category: str = Query(default="", description="Category to scope book facets to."),
    book: str = Query(default="", description="Book to scope volume facets to."),
) -> SearchFacets:
    """Return the categories, books, and volumes that hold matches for ``q``."""
    return corpus_repo.facets(q=q, mode=mode, category=category, book=book)


async def _search_books(
    page: Annotated[PageParams, Depends()],
    q: str = Query(default="", description="Title or author text; folded before matching."),
    field: Annotated[SearchField, Query(description="Match field: title, author, or any.")] = "any",
) -> Page[Book]:
    """Wrap the repo's (slice, total) into a Page[Book] envelope."""
    items, total = books_repo.search_books(q=q, field=field, limit=page.limit, offset=page.offset)
    return Page[Book](items=items, total=total, limit=page.limit, offset=page.offset)


router.add_api_route(
    "/search",
    _search,
    methods=["GET"],
    response_model=Page[CorpusMatch],
    status_code=status.HTTP_200_OK,
    summary="Full-text search across all book content (diacritic-insensitive).",
)
router.add_api_route(
    "/search/facets",
    _search_facets,
    methods=["GET"],
    response_model=SearchFacets,
    status_code=status.HTTP_200_OK,
    summary="Category -> book -> volume filters available for a search query.",
)
router.add_api_route(
    "/search/books",
    _search_books,
    methods=["GET"],
    response_model=Page[Book],
    status_code=status.HTTP_200_OK,
    summary="Search book metadata by title / author (diacritic-insensitive).",
)
