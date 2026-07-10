"""HTTP routes for enriched narrator persons: paginated list + detail + relations + events + grades.

The list handler filters + wraps the repo's ``(slice, total)`` into a ``Page``
envelope and takes the shared ``PageParams``; the detail, edges, events, and
grades routes bind their repo functions directly (person id from the path).
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.api._pagination import PageDep
from backend.api._routes import as_page, get_route
from backend.models.narrator import PersonEdge, PersonEntry, PersonEvent, PersonGrade
from backend.models.pagination import Page
from backend.repositories import registry

router = APIRouter(tags=["person"])


async def _list_person(
    page: PageDep,
    q: str = Query(default="", description="Substring match on name / kunya / nisba / variants."),
    tradition: str = Query(default="", description="Filter by tradition (sunni / shia / both)."),
    confidence: str = Query(default="", description="Filter by record confidence (high / medium)."),
    has_events: bool = Query(default=False, description="Only persons with historical events."),
) -> Page[PersonEntry]:
    """Wrap the repo's (slice, total) into a Page[PersonEntry] envelope."""
    return as_page(
        Page[PersonEntry],
        page,
        registry.list_person(
            registry.PersonFilter(
                q=q,
                tradition=tradition,
                confidence=confidence,
                has_events=has_events,
            ),
            limit=page.limit,
            offset=page.offset,
        ),
    )


get_route(
    router,
    "/person",
    _list_person,
    response_model=Page[PersonEntry],
    summary="List enriched narrator persons with pagination + filters.",
)
get_route(
    router,
    "/person/{person_id}",
    registry.get_person,
    response_model=PersonEntry,
    summary="Get a single enriched person by id.",
)
get_route(
    router,
    "/person/{person_id}/edges",
    registry.get_person_edges,
    response_model=list[PersonEdge],
    summary="Get a person's teacher/student relations.",
)
get_route(
    router,
    "/person/{person_id}/events",
    registry.get_person_events,
    response_model=list[PersonEvent],
    summary="Get the historical events attributed to a person.",
)
get_route(
    router,
    "/person/{person_id}/grades",
    registry.get_person_grades,
    response_model=list[PersonGrade],
    summary="Get a person's source-validated reliability grades with reader links.",
)
