"""HTTP routes for cross-corpus full-text search + facet lookups.

All routes register via ``add_api_route``. ``/search`` is the content search
(full-text over page text, ``exact``/``broad`` mode, filtered by category -> book ->
volume) -> ``Page[CorpusMatch]``. ``/search/facets`` returns the categories/
books/volumes that have matches. The paginated routes take the shared
``PageParams``. Catalog search lives on ``/works?q=`` (volume-folded works);
narrators are searched via the rijal route.

``SearchMode`` is a closed ``Literal`` set, so FastAPI rejects an unknown mode
with 422 rather than the repo silently defaulting it to ``exact``.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from backend.api._pagination import PageDep
from backend.api._routes import as_page, get_route
from backend.api._validation import reject_unknown
from backend.models.errors import ErrorEnvelope
from backend.models.pagination import Page
from backend.models.search import CorpusMatch, SearchFacets, SearchMode
from backend.query_language import QueryLanguageError
from backend.repositories import _taxonomy
from backend.repositories import corpus as corpus_repo
from backend.repositories import semantic as semantic_repo

router = APIRouter(tags=["search"])

_MODE_DESC = "Match mode: 'exact' (whole phrase) or 'broad' (sub-phrases)."


_CATEGORY_DESC = "Restrict to these category slugs (repeatable; values OR together)."


def _checked_categories(category: list[str] | None) -> tuple[str, ...]:
    """Validate every repeated ``category`` value against the taxonomy (422 on
    an unknown slug) and freeze the set for the repo query. ``None`` is the
    absent-param default and means no category constraint."""
    if category is None:
        return ()
    for slug in category:
        reject_unknown("category", slug, _taxonomy.is_known_category)
    return tuple(category)


class SearchParams:
    """Corpus content-search query + scope filters as request parameters."""

    def __init__(
        self,
        q: str = Query(default="", description="Arabic phrase; folded before matching."),
        mode: Annotated[SearchMode, Query(description=_MODE_DESC)] = "exact",
        category: Annotated[list[str] | None, Query(description=_CATEGORY_DESC)] = None,
        book: str = Query(default="", description="Restrict to a book title (a work)."),
        volume: int = Query(default=0, ge=0, description="Restrict to a volume number (0 = any)."),
    ) -> None:
        self.query = corpus_repo.SearchQuery(
            q=q, mode=mode, categories=_checked_categories(category), book=book, volume=volume
        )


async def _search(
    page: PageDep,
    params: Annotated[SearchParams, Depends()],
) -> Page[CorpusMatch]:
    """Wrap the repo's (slice, total) into a Page[CorpusMatch] envelope."""
    return as_page(
        Page[CorpusMatch],
        page,
        await corpus_repo.search(params.query, limit=page.limit, offset=page.offset),
    )


async def _search_facets(
    q: str = Query(default="", description="Arabic phrase; folded before matching."),
    mode: Annotated[SearchMode, Query(description=_MODE_DESC)] = "exact",
    category: Annotated[list[str] | None, Query(description=_CATEGORY_DESC)] = None,
    book: str = Query(default="", description="Book to scope volume facets to."),
) -> SearchFacets:
    """Return the categories, books, and volumes that hold matches for ``q``."""
    return await corpus_repo.facets(
        q=q, mode=mode, categories=_checked_categories(category), book=book
    )


_SEARCH_503: dict[int | str, dict[str, Any]] = {
    503: {
        "model": ErrorEnvelope,
        "description": "The consolidated search backend is unreachable or answered "
        "outside contract.",
    }
}


get_route(
    router,
    "/search",
    _search,
    response_model=Page[CorpusMatch],
    summary="Full-text search across all book content (diacritic-insensitive).",
    responses=_SEARCH_503,
)
get_route(
    router,
    "/search/facets",
    _search_facets,
    response_model=SearchFacets,
    summary="Category -> book -> volume filters available for a search query.",
    responses=_SEARCH_503,
)

_SEMANTIC_RESPONSES: dict[int | str, dict[str, Any]] = {
    502: {
        "model": ErrorEnvelope,
        "description": "The LLM planner failed, answered outside contract, or "
        "produced no usable plan.",
    },
    503: {
        "model": ErrorEnvelope,
        "description": "LLM search is not configured (SOL_LLM_API_KEY missing) "
        "or the consolidated search backend is unreachable.",
    },
}


async def _search_semantic(
    page: PageDep,
    q: str = Query(
        default="",
        description="Freeform query, usually English; planned by the LLM, "
        "executed by the corpus engine.",
    ),
    category: Annotated[list[str] | None, Query(description=_CATEGORY_DESC)] = None,
    book: Annotated[str, Query(description="Restrict the plan to a book title.")] = "",
) -> Page[CorpusMatch]:
    """Wrap the semantic repo's (slice, total) into the shared Page envelope.

    The response model is the corpus search's own ``Page[CorpusMatch]``: a
    semantic hit and a keyword hit are the same object by construction. A
    blank query is the caller's error (422), matching the boolean-grammar
    guard's contract.
    """
    if not q.strip():
        raise QueryLanguageError("a semantic search needs a non-empty query")
    return as_page(
        Page[CorpusMatch],
        page,
        await semantic_repo.search_planned(
            q,
            limit=page.limit,
            offset=page.offset,
            categories=_checked_categories(category),
            book=book,
        ),
    )


get_route(
    router,
    "/search/semantic",
    _search_semantic,
    response_model=Page[CorpusMatch],
    summary="LLM-planned search: a freeform question in, corpus matches out.",
    responses=_SEMANTIC_RESPONSES,
)


async def _semantic_facets(
    q: str = Query(
        default="",
        description="The semantic query whose executed plan is faceted.",
    ),
    category: Annotated[list[str] | None, Query(description=_CATEGORY_DESC)] = None,
    book: Annotated[str, Query(description="Book to scope book facets to.")] = "",
) -> SearchFacets:
    """Drill-down facets for an executed semantic plan (categories, books)."""
    if not q.strip():
        raise QueryLanguageError("a semantic facets lookup needs a non-empty query")
    return await semantic_repo.planned_facets(
        q, categories=_checked_categories(category), book=book
    )


get_route(
    router,
    "/search/semantic/facets",
    _semantic_facets,
    response_model=SearchFacets,
    summary="Category -> book filters available for an LLM-planned search.",
    responses=_SEMANTIC_RESPONSES,
)
