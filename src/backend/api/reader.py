"""HTTP routes for the reader: TOC + page content + in-book search.

All routes register via ``add_api_route`` (the project's one registration
style). TOC + page bind repository functions directly; 404s come from the
global ResourceNotFoundError handler in ``main.py``. In-book search delegates
to the one corpus search engine (``repositories.corpus``) scoped to the book's
URN, then projects each hit's page + snippet into a ``Page[BookSearchMatch]``.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.core.constants import HTTP__MAX_PAGE_SIZE, READER__SEARCH_DEFAULT_LIMIT
from backend.core.http import status
from backend.models.pagination import Page
from backend.models.reader import BookPage, BookSearchMatch, Toc
from backend.repositories import corpus as corpus_repo
from backend.repositories import reader as reader_repo

router = APIRouter(tags=["reader"])


async def _search_book(
    book_urn: str,
    q: str = Query(default="", description="Arabic query; folded before matching."),
    limit: int = Query(
        default=READER__SEARCH_DEFAULT_LIMIT,
        ge=1,
        le=HTTP__MAX_PAGE_SIZE,
        description="Matches per page.",
    ),
    offset: int = Query(default=0, ge=0, description="Matches to skip."),
) -> Page[BookSearchMatch]:
    """Run the corpus engine scoped to ``book_urn`` and project page + snippet."""
    items, total = corpus_repo.search(q=q, urn=book_urn, limit=limit, offset=offset)
    matches = [BookSearchMatch(page=m.page, snippet=m.snippet) for m in items]
    return Page[BookSearchMatch](items=matches, total=total, limit=limit, offset=offset)


router.add_api_route(
    "/books/{book_urn}/toc",
    reader_repo.get_toc,
    methods=["GET"],
    response_model=Toc,
    status_code=status.HTTP_200_OK,
    summary="Get the table of contents for a book.",
)
router.add_api_route(
    "/books/{book_urn}/pages/{page_number}",
    reader_repo.get_page,
    methods=["GET"],
    response_model=BookPage,
    status_code=status.HTTP_200_OK,
    summary="Get one page of book content.",
)
router.add_api_route(
    "/books/{book_urn}/search",
    _search_book,
    methods=["GET"],
    response_model=Page[BookSearchMatch],
    status_code=status.HTTP_200_OK,
    summary="Search within a book's text (diacritic- + letter-variant-insensitive).",
)
