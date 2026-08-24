"""The one GET-route registration idiom and the page-envelope constructor.

Every route in this API is a GET returning 200 with an explicit response
model; ``get_route`` states that convention once instead of every router
repeating ``methods=["GET"]`` and ``status_code``. ``as_page`` wraps a
repository's ``(slice, total)`` tuple into the parametrized ``Page`` envelope
that every list handler used to assemble by hand. ``NOT_FOUND_404`` lets a
router whose routes can answer ResourceNotFoundError declare the shared 404
once at router level (APIRouter responses merge into every route), so the
contract says what the handler actually does without per-route repetition.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from backend.api._pagination import PageParams
from backend.core.http import status
from backend.models.errors import ErrorEnvelope
from backend.models.pagination import Page

NOT_FOUND_404: dict[int | str, dict[str, Any]] = {
    404: {
        "model": ErrorEnvelope,
        "description": "The requested resource does not exist (unknown urn, id, surah, or ayah).",
    }
}


def get_route(
    router: APIRouter,
    path: str,
    endpoint: Callable[..., Any],
    *,
    response_model: Any,
    summary: str,
    responses: dict[int | str, dict[str, Any]] | None = None,
) -> None:
    """Register ``endpoint`` at ``path`` with the project's GET/200 idiom.

    ``responses`` declares the route's expected failure responses (e.g. a 503
    from the search proxy) so they appear in the exported OpenAPI schema and
    the generated frontend types. Shaped as FastAPI's OpenAPI response dict:
    status -> {model, description}."""
    router.add_api_route(
        path,
        endpoint,
        methods=["GET"],
        response_model=response_model,
        status_code=status.HTTP_200_OK,
        summary=summary,
        responses=responses,
    )


def as_page[T](model: type[Page[T]], page: PageParams, result: tuple[list[T], int]) -> Page[T]:
    """Wrap a repository's ``(slice, total)`` into the given ``Page`` envelope.

    Takes the parametrized envelope class so pydantic validates the items
    against the concrete model at construction, exactly as the hand-written
    envelopes did.
    """
    items, total = result
    return model(items=items, total=total, limit=page.limit, offset=page.offset)
