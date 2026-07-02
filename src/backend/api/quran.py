"""HTTP routes for the Qurʾān: verse lookup by reference, and verse search by term.

``/quran/{surah}/{ayah}`` resolves a reference (e.g. ``68/4``) to its verse text
-> ``Ayah``; an out-of-range surah or ayah 404s via the global
``ResourceNotFoundError`` handler in ``main.py``. ``/quran/search?q=`` returns the
``Page[Ayah]`` of verses whose text contains a folded Arabic term. The frontend's
Qurʾān scope routes a ``NN:NN`` query to the lookup (then drives the content search
to surface passages quoting the verse) and any other query to the term search.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.api._pagination import PageDep
from backend.api._routes import as_page, get_route
from backend.models.pagination import Page
from backend.models.quran import Ayah, Surah
from backend.repositories import quran as quran_repo

router = APIRouter(tags=["quran"])


async def _search_verses(
    page: PageDep,
    q: str = Query(default="", description="Arabic term or phrase to find in the Qurʾān."),
) -> Page[Ayah]:
    """Wrap the repo's ``(slice, total)`` of matching ayat into a Page[Ayah]."""
    return as_page(
        Page[Ayah], page, quran_repo.search_verses(q=q, limit=page.limit, offset=page.offset)
    )


get_route(
    router,
    "/quran/search",
    _search_verses,
    response_model=Page[Ayah],
    summary="Find Qurʾān verses containing an Arabic term or phrase.",
)

get_route(
    router,
    "/quran/{surah}",
    quran_repo.get_surah,
    response_model=Surah,
    summary="Resolve a full surah to its numbered ayat, in order.",
)

get_route(
    router,
    "/quran/{surah}/{ayah}",
    quran_repo.get_verse,
    response_model=Ayah,
    summary="Resolve a Qurʾān verse by surah:ayah reference.",
)
