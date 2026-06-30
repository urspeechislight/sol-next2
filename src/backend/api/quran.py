"""HTTP routes for the Qurʾān: verse lookup by reference, and verse search by term.

``/quran/{surah}/{ayah}`` resolves a reference (e.g. ``68/4``) to its verse text
-> ``Ayah``; an out-of-range surah or ayah 404s via the global
``ResourceNotFoundError`` handler in ``main.py``. ``/quran/search?q=`` returns the
``Page[Ayah]`` of verses whose text contains a folded Arabic term. The frontend's
Qurʾān scope routes a ``NN:NN`` query to the lookup (then drives the content search
to surface passages quoting the verse) and any other query to the term search.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageParams
from backend.core.http import status
from backend.models.pagination import Page
from backend.models.quran import Ayah
from backend.repositories import quran as quran_repo

router = APIRouter(tags=["quran"])


async def _search_verses(
    page: Annotated[PageParams, Depends()],
    q: str = Query(default="", description="Arabic term or phrase to find in the Qurʾān."),
) -> Page[Ayah]:
    """Wrap the repo's ``(slice, total)`` of matching ayat into a Page[Ayah]."""
    items, total = quran_repo.search_verses(q=q, limit=page.limit, offset=page.offset)
    return Page[Ayah](items=items, total=total, limit=page.limit, offset=page.offset)


router.add_api_route(
    "/quran/search",
    _search_verses,
    methods=["GET"],
    response_model=Page[Ayah],
    status_code=status.HTTP_200_OK,
    summary="Find Qurʾān verses containing an Arabic term or phrase.",
)

router.add_api_route(
    "/quran/{surah}/{ayah}",
    quran_repo.get_verse,
    methods=["GET"],
    response_model=Ayah,
    status_code=status.HTTP_200_OK,
    summary="Resolve a Qurʾān verse by surah:ayah reference.",
)
