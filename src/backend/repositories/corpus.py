"""Cross-corpus content search, proxied to the consolidated search backend.

The served cross-corpus search (CENTRAL-005). This module is a thin async HTTP
client over the single consolidated search backend that owns the page index, so
adding a book there is enough for it to appear in this search with no local
rebuild. The query, match mode (``exact`` whole phrase / ``broad`` sub-phrase
windows), and the category -> book -> volume scope filters are forwarded as-is;
the backend folds the query, runs the index lookup, and builds the snippet. Each
backend hit is mapped one-to-one onto ``CorpusMatch`` (the reader-facing page
field is the backend's ``page_number``).

The in-book scan stays a separate, local path (``search_in_book``): a single
open book is scanned in memory against the shared fold + snippet helpers, since
it reads the reader page store rather than the global index. ``search_windows``
is the one place a query becomes match windows and is shared by both paths; here
it also doubles as the blank-query guard, because a query that folds to nothing
has no windows and short-circuits to an empty result with no backend round-trip.

Backend failures surface as ``CorpusSearchError``. The proxy makes exactly one
request to one backend and reports any failure rather than hiding it.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Final

import httpx

from backend.core.constants import (
    CORPUS__SNIPPET_HEAD_CHARS,
    CORPUS__SNIPPET_WINDOW_CHARS,
    HTTP__DEFAULT_PAGE_SIZE,
    HTTP__REQUEST_TIMEOUT_SECONDS,
)
from backend.core.settings import get_settings
from backend.models.reader import BookSearchMatch
from backend.models.search import (
    BookFacet,
    CategoryFacet,
    CorpusMatch,
    SearchFacets,
    SearchMode,
    VolumeFacet,
)
from backend.patterns import fold_search
from backend.repositories import reader as reader_repo
from backend.repositories._data_loader import slice_page

_BROAD_WINDOW: Final[int] = 4


class CorpusSearchError(RuntimeError):
    """Raised when the consolidated search backend fails or answers outside contract.

    Carries enough context to debug the failure; the API layer lets it propagate
    as a 5xx so a backend outage is visible rather than silently swallowed.
    """


@lru_cache(maxsize=1)
def _client() -> httpx.AsyncClient:
    """Return the process-wide async client bound to the search backend base URL.

    Reused across requests for connection pooling. The base URL comes from
    ``Settings.corpus_search_base_url`` so a deployment points the reader at its
    co-located backend without a code change.
    """
    return httpx.AsyncClient(
        base_url=get_settings().corpus_search_base_url,
        timeout=HTTP__REQUEST_TIMEOUT_SECONDS,
    )


async def _fetch_json(path: str, params: dict[str, Any]) -> dict[str, Any]:
    """GET one JSON object from the search backend, surfacing any failure.

    The single network seam: every backend call goes through here, so the mapping
    functions stay pure and tests swap behavior by replacing ``_client``.
    """
    try:
        response = await _client().get(path, params=params)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise CorpusSearchError(f"search backend {path} request failed: {exc}") from exc
    try:
        data = response.json()
    except ValueError as exc:
        raise CorpusSearchError(f"search backend {path} returned non-JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise CorpusSearchError(f"search backend {path} returned non-object JSON")
    return data


def search_windows(q: str, mode: SearchMode) -> list[str]:
    """Fold the query and return the phrase windows to match + locate.

    ``exact`` -> one window (the whole phrase). ``broad`` -> overlapping
    ``_BROAD_WINDOW`` word windows when the query is longer than one window, else
    the whole phrase. Empty query -> ``[]``. Shared by the proxied corpus search
    and the in-book page scan, and reused as the blank-query guard for the proxy
    path.

    ``_BROAD_WINDOW`` is 4: four consecutive words stay distinctive enough that
    even a long, common-worded verse matches only a few hundred pages, whereas a
    two-word window matched millions.
    """
    words = [w for w in fold_search(q).replace('"', " ").split() if w]
    if not words:
        return []
    if mode == "broad" and len(words) > _BROAD_WINDOW:
        return [
            " ".join(words[i : i + _BROAD_WINDOW]) for i in range(len(words) - _BROAD_WINDOW + 1)
        ]
    return [" ".join(words)]


def _fold_with_map(text: str) -> tuple[str, list[int]]:
    """Fold ``text`` for matching while recording each folded character's origin.

    For each folded character, record the index of the original character it came
    from. Folding drops marks and 1:1-replaces letters, so each folded position
    maps to exactly one original position, enough to slice an excerpt of the
    original around a folded hit.
    """
    folded: list[str] = []
    origin: list[int] = []
    for i, ch in enumerate(text):
        f = fold_search(ch)
        if f:
            folded.append(f)
            origin.append(i)
    return "".join(folded), origin


def locate_snippet(content: str, windows: list[str]) -> tuple[bool, str]:
    """Locate the first folded ``windows`` hit and return ``(found, snippet)``.

    The snippet is a fold-aware excerpt keeping original orthography, or
    ``(False, head)`` when no window is present. The one place the fold-aware
    snippet is built; shared by the in-book scan (the proxied path uses the
    backend's snippet).
    """
    folded, origin = _fold_with_map(content)
    for needle in windows:
        hit = folded.find(needle)
        if hit < 0:
            continue
        start = origin[hit]
        end = origin[hit + len(needle) - 1] + 1
        left = max(0, start - CORPUS__SNIPPET_WINDOW_CHARS)
        right = min(len(content), end + CORPUS__SNIPPET_WINDOW_CHARS)
        prefix = "…" if left > 0 else ""
        suffix = "…" if right < len(content) else ""
        return True, f"{prefix}{content[left:right]}{suffix}"
    head = content[:CORPUS__SNIPPET_HEAD_CHARS]
    if len(content) > CORPUS__SNIPPET_HEAD_CHARS:
        return False, f"{head}…"
    return False, head


@dataclass(frozen=True, slots=True)
class SearchQuery:
    """The query text + scope filters for a cross-corpus content search."""

    q: str = ""
    mode: SearchMode = "exact"
    categories: tuple[str, ...] = ()
    book: str = ""
    volume: int = 0


async def search(
    query: SearchQuery,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[CorpusMatch], int]:
    """Return ``(slice, total)`` of corpus pages matching ``query`` + filters.

    Forwards the query, mode, and category/book/volume scope to the consolidated
    search backend, which folds the query, runs the index lookup, and returns a
    bounded total plus the page window. Each backend hit is mapped onto a
    ``CorpusMatch``: the reader's ``page`` is the backend's ``page_number``. A
    query that folds to nothing (blank, or marks only) short-circuits to an empty
    result without a round-trip, matching the in-book path.
    """
    if not search_windows(query.q, query.mode):
        return [], 0
    params: dict[str, Any] = {
        "q": query.q,
        "mode": query.mode,
        "category": list(query.categories),
        "book": query.book,
        "volume": query.volume,
        "limit": limit,
        "offset": offset,
        "include_count": "true",
    }
    data = await _fetch_json("/api/search", params)
    items = data.get("items", [])
    if not isinstance(items, list):
        raise CorpusSearchError("search backend /api/search returned non-list items")
    matches = [
        CorpusMatch(
            urn=item["urn"],
            title_ar=item.get("title_ar") or item["urn"],
            title_en=item.get("title_en"),
            author=item.get("author"),
            category=item.get("category") or "",
            volume=item.get("volume"),
            page=item["page_number"],
            snippet=item["snippet"],
        )
        for item in items
        if isinstance(item, dict)
    ]
    total = data.get("total")
    if not isinstance(total, int):
        raise CorpusSearchError("search backend /api/search returned no bounded total")
    return matches, total


async def facets(
    q: str = "",
    mode: SearchMode = "exact",
    categories: tuple[str, ...] = (),
    book: str = "",
) -> SearchFacets:
    """Drill-down facets for the active match mode, proxied from the backend.

    Categories over the query, books within the selected category set, and
    volumes within the chosen book. A blank query short-circuits to empty facets
    without a backend round-trip.
    """
    if not search_windows(q, mode):
        return SearchFacets(categories=[], books=[], volumes=[])
    params: dict[str, Any] = {
        "q": q,
        "mode": mode,
        "category": list(categories),
        "book": book,
    }
    data = await _fetch_json("/api/search/facets", params)
    return SearchFacets(
        categories=[
            CategoryFacet(slug=c["slug"], count=c["count"])
            for c in data.get("categories", [])
            if isinstance(c, dict)
        ],
        books=[
            BookFacet(title=b["title"], title_en=b.get("title_en"), count=b["count"])
            for b in data.get("books", [])
            if isinstance(b, dict)
        ],
        volumes=[
            VolumeFacet(volume=v["volume"], count=v["count"])
            for v in data.get("volumes", [])
            if isinstance(v, dict)
        ],
    )


def search_in_book(
    book_urn: str,
    q: str,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[BookSearchMatch], int]:
    """Return ``(slice, total)`` of pages in ``book_urn`` matching a query window.

    Each matching page carries a fold-aware snippet. Scans the book's own pages in
    memory (via ``reader.page_rows``, the page SSOT) rather than the global index:
    a single book is small enough to scan, and this path is independent of the
    cross-corpus backend. Shares ``search_windows`` + ``locate_snippet`` with the
    proxied path so the fold and snippet logic lives once.
    """
    windows = search_windows(q, "exact")
    if not windows:
        return [], 0
    matches: list[BookSearchMatch] = []
    for row in reader_repo.page_rows(book_urn):
        found, snippet = locate_snippet(row.content, windows)
        if found:
            matches.append(BookSearchMatch(page=row.page, snippet=snippet))
    return slice_page(matches, limit, offset)
