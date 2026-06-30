"""HTTP routes for books: paginated list + detail.

Both routes register via ``add_api_route``. The list handler transforms the
repo's ``(slice, total)`` tuple into a ``Page[Book]`` envelope and takes the
shared ``PageParams``; the detail route binds ``books_repo.get_book`` directly,
with 404s from the global handler.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageParams
from backend.core.http import status
from backend.models.book import Book
from backend.models.pagination import Page
from backend.repositories import books as books_repo

router = APIRouter(tags=["books"])


async def _list_books(
    page: Annotated[PageParams, Depends()],
    category: str | None = Query(default=None, description="Filter by category slug."),
) -> Page[Book]:
    """Wrap the repo's (slice, total) into a Page[Book] envelope."""
    items, total = books_repo.list_books(category=category, limit=page.limit, offset=page.offset)
    return Page[Book](items=items, total=total, limit=page.limit, offset=page.offset)


router.add_api_route(
    "/books",
    _list_books,
    methods=["GET"],
    response_model=Page[Book],
    status_code=status.HTTP_200_OK,
    summary="List books with pagination, optionally filtered by category slug.",
)
router.add_api_route(
    "/books/{urn}",
    books_repo.get_book,
    methods=["GET"],
    response_model=Book,
    status_code=status.HTTP_200_OK,
    summary="Get a single book by URN.",
)
