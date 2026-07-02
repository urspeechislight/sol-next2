"""The one GET-route registration idiom and the page-envelope constructor.

Every route in this API is a GET returning 200 with an explicit response
model; ``get_route`` states that convention once instead of every router
repeating ``methods=["GET"]`` and ``status_code``. ``as_page`` wraps a
repository's ``(slice, total)`` tuple into the parametrized ``Page`` envelope
that every list handler used to assemble by hand.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from backend.api._pagination import PageParams
from backend.core.http import status
from backend.models.pagination import Page


def get_route(
    router: APIRouter,
    path: str,
    endpoint: Callable[..., Any],
    *,
    response_model: Any,
    summary: str,
) -> None:
    """Register ``endpoint`` at ``path`` with the project's GET/200 idiom."""
    router.add_api_route(
        path,
        endpoint,
        methods=["GET"],
        response_model=response_model,
        status_code=status.HTTP_200_OK,
        summary=summary,
    )


def as_page[T](model: type[Page[T]], page: PageParams, result: tuple[list[T], int]) -> Page[T]:
    """Wrap a repository's ``(slice, total)`` into the given ``Page`` envelope.

    Takes the parametrized envelope class so pydantic validates the items
    against the concrete model at construction, exactly as the hand-written
    envelopes did.
    """
    items, total = result
    return model(items=items, total=total, limit=page.limit, offset=page.offset)
