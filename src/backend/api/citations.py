"""HTTP routes for the Qur'an citation sidecar: per-page linkable citations.

Registers via ``get_route`` (CENTRAL-004 keeps route decorators in this
package). The per-page route backs the reader's in-text verse links; the
concordance route exposes the reverse index the sidecar was built to enable.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.api._routes import get_route
from backend.core.constants import QURAN__SURAH_COUNT
from backend.models.citation import Citation
from backend.repositories import citations as citations_repo

router = APIRouter(tags=["citations"])


async def _page_citations(urn: str, page: int) -> list[Citation]:
    """Verse-verified Qur'an citations on one page, ordered by position."""
    return citations_repo.page_citations(urn, page)


async def _books_citing(surah: int, aya: int) -> dict[str, int]:
    """Reverse concordance: how many distinct books cite ``surah:aya``."""
    surah = min(max(surah, 1), QURAN__SURAH_COUNT)
    return {"books": citations_repo.books_citing(surah, aya)}


get_route(
    router,
    "/books/{urn}/pages/{page}/citations",
    _page_citations,
    response_model=list[Citation],
    summary="Auto-linkable Qur'an citations located in a page's text.",
)
get_route(
    router,
    "/citations/{surah}/{aya}/books",
    _books_citing,
    response_model=dict[str, int],
    summary="Count of distinct books citing a given surah:aya (reverse concordance).",
)
