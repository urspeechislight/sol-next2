"""HTTP routes for books: paginated list, detail, and sibling volumes.

All routes register via ``add_api_route``. The list handler transforms the
repo's ``(slice, total)`` tuple into a ``Page[Book]`` envelope and takes the
shared ``PageParams``; the detail and volumes routes bind their repo functions
directly, with 404s from the global handler.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.api._pagination import PageDep
from backend.api._routes import as_page, get_route
from backend.models.book import Book
from backend.models.pagination import Page
from backend.repositories import books as books_repo

router = APIRouter(tags=["books"])


async def _list_books(
    page: PageDep,
    category: str | None = Query(default=None, description="Filter by category slug."),
) -> Page[Book]:
    """Wrap the repo's (slice, total) into a Page[Book] envelope."""
    return as_page(
        Page[Book],
        page,
        books_repo.list_books(category=category, limit=page.limit, offset=page.offset),
    )


get_route(
    router,
    "/books",
    _list_books,
    response_model=Page[Book],
    summary="List books with pagination, optionally filtered by category slug.",
)
get_route(
    router,
    "/books/{urn}",
    books_repo.get_book,
    response_model=Book,
    summary="Get a single book by URN.",
)
get_route(
    router,
    "/books/{urn}/volumes",
    books_repo.list_volumes,
    response_model=list[Book],
    summary="List every volume of the work containing this book, ascending.",
)
