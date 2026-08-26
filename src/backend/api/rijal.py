"""HTTP routes for the narrator registry: paginated list + detail + graph.

All routes register via ``get_route``. The list handler filters + wraps the
repo's ``(slice, total)`` into a ``Page[NarratorEntry]`` envelope and takes the
shared ``PageParams``; the detail and graph routes bind their repo functions
directly (narrator id from the path). The graph route clamps ``depth`` to the
project's 1..3 band before delegating to the recursive-CTE walk.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageDep
from backend.api._routes import NOT_FOUND_404, as_page, get_route
from backend.core.constants import (
    NARRATORS__GRAPH_DEFAULT_DEPTH,
    NARRATORS__GRAPH_MAX_DEPTH,
)
from backend.models.narrator import NarratorDetail, NarratorEntry, NarratorGraph
from backend.models.pagination import Page
from backend.repositories import registry

router = APIRouter(tags=["narrators"], responses=NOT_FOUND_404)


class NarratorFilterParams:
    """Narrator listing filters as request query parameters."""

    def __init__(
        self,
        q: str = Query(
            default="",
            description=(
                "Substring match on the narrator's names. Matched against the "
                "normalized alias store (diacritics stripped, letter variants "
                "folded, ابن folded to بن) and, as a second pass, the raw "
                "primary Arabic name."
            ),
        ),
        category: str = Query(
            default="", description="Filter by data-quality category (clean, long_entry)."
        ),
        tradition: str = Query(
            default="", description="Filter by tradition (imami / shafii / hanafi / ...)."
        ),
    ) -> None:
        self.filter = registry.NarratorFilter(q=q, category=category, tradition=tradition)


async def _list_narrators(
    page: PageDep,
    filters: Annotated[NarratorFilterParams, Depends()],
) -> Page[NarratorEntry]:
    """Wrap the repo's (slice, total) into a Page[NarratorEntry] envelope."""
    return as_page(
        Page[NarratorEntry],
        page,
        registry.list_narrators(filters.filter, limit=page.limit, offset=page.offset),
    )


def _graph(
    narrator_id: int,
    direction: str = Query(
        default="students",
        pattern="^(students|teachers)$",
        description="'students' (taught by the narrator) or 'teachers' (taught him).",
    ),
    depth: int = Query(
        default=NARRATORS__GRAPH_DEFAULT_DEPTH,
        ge=1,
        le=NARRATORS__GRAPH_MAX_DEPTH,
        description="Relation hops to expand from the root.",
    ),
) -> NarratorGraph:
    """Clamp and delegate: the recursive-CTE walk lives in the repository."""
    return registry.get_narrator_graph(narrator_id, direction, depth)


get_route(
    router,
    "/narrators",
    _list_narrators,
    response_model=Page[NarratorEntry],
    summary="List narrators with pagination + filters.",
)
get_route(
    router,
    "/narrators/{narrator_id}",
    registry.get_narrator,
    response_model=NarratorDetail,
    summary="Get a single narrator's full record by id.",
)
get_route(
    router,
    "/narrators/{narrator_id}/graph",
    _graph,
    response_model=NarratorGraph,
    summary="Expand a narrator's student or teacher relations to a bounded depth.",
)
