"""HTTP routes for the reader: TOC + page content + in-book search.

All routes register via ``add_api_route`` (the project's one registration
style). TOC + page bind repository functions directly; 404s come from the
global ResourceNotFoundError handler in ``main.py``. In-book search delegates
to the one corpus search engine (``repositories.corpus``) scoped to the book's
URN, then projects each hit's page + snippet into a ``Page[BookSearchMatch]``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageParams, page_params
from backend.api._routes import as_page, get_route
from backend.core.constants import READER__SEARCH_DEFAULT_LIMIT
from backend.models.pagination import Page
from backend.models.reader import BookPage, BookSearchMatch, Toc
from backend.repositories import corpus as corpus_repo
from backend.repositories import reader as reader_repo

router = APIRouter(tags=["reader"])

_reader_page_params = page_params(
    default_limit=READER__SEARCH_DEFAULT_LIMIT,
    limit_description="Matches per page.",
    offset_description="Matches to skip.",
)


async def _search_book(
    book_urn: str,
    q: str = Query(default="", description="Arabic query; folded before matching."),
    *,
    page: Annotated[PageParams, Depends(_reader_page_params)],
) -> Page[BookSearchMatch]:
    """Scan ``book_urn``'s own pages for ``q`` (the in-memory path; see
    ``repositories.corpus.search_in_book``) and wrap the matches in a page."""
    return as_page(
        Page[BookSearchMatch],
        page,
        corpus_repo.search_in_book(book_urn, q=q, limit=page.limit, offset=page.offset),
    )


get_route(
    router,
    "/books/{book_urn}/toc",
    reader_repo.get_toc,
    response_model=Toc,
    summary="Get the table of contents for a book.",
)
get_route(
    router,
    "/books/{book_urn}/pages/{page_number}",
    reader_repo.get_page,
    response_model=BookPage,
    summary="Get one page of book content.",
)
get_route(
    router,
    "/books/{book_urn}/search",
    _search_book,
    response_model=Page[BookSearchMatch],
    summary="Search within a book's text (diacritic- + letter-variant-insensitive).",
)
