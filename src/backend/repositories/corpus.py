"""Read-only repository for the corpus full-text index — backed by ``data/corpus.db``.

The served cross-corpus content search (CENTRAL-005). The FTS5 index stores each
page TWICE: a ``fold`` column (text put through ``patterns.fold_search`` —
diacritics + annotation signs removed, alef/yaa/taa letter variants folded)
which is the matched column, and an UNINDEXED ``content`` column holding the
original text for display. The query is folded the same way, so a search is
insensitive to diacritics AND letter-variant spelling; snippets are then built
from the original ``content`` (fold-aware), so results keep true manuscript
orthography. A small ``book(urn, category, title, volume)`` table (joined by URN)
backs the category-set -> book -> volume filters: the repeated ``category``
params arrive as a set (a UI domain pick is already expanded to its categories
by the client's taxonomy) and bind as one JSON array ``:cats`` through
``json_each``, so the SQL stays constant. Two match modes: ``exact`` (the
whole phrase) and ``broad`` (OR of the query's overlapping fixed-width word
windows — finds sub-phrases). Opened read-only + immutable at serve; the DDL +
INSERT helpers that build it live in ``backend.build.corpus``.

The bounded count queries ``_COUNT_UNFILTERED`` / ``_COUNT_FILTERED`` are each
built from the constant ``_FILTER`` and run with bound parameters (``:q``,
``:cap``, ``:limit``), never from interpolated input, so Bandit's S608 warning
on them is a false positive and is suppressed inline.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Final

from backend.core.constants import (
    ARTIFACT__CORPUS_DB,
    CORPUS__SNIPPET_HEAD_CHARS,
    CORPUS__SNIPPET_WINDOW_CHARS,
    HTTP__DEFAULT_PAGE_SIZE,
)
from backend.core.logging import get_logger
from backend.models.book import Book
from backend.models.reader import BookSearchMatch
from backend.models.search import (
    BookFacet,
    CategoryFacet,
    CorpusMatch,
    SearchFacets,
    SearchMode,
    VolumeFacet,
)
from backend.patterns import fold_search, fold_with_offsets
from backend.repositories import books as books_repo
from backend.repositories import reader as reader_repo
from backend.repositories._data_loader import open_ro_db, slice_page

_logger = get_logger("shia-library.corpus")

_BROAD_WINDOW: Final[int] = 4

_FILTER = (
    "FROM pages JOIN book ON book.urn = pages.urn "
    "WHERE pages MATCH :q "
    "  AND (:cats = '' OR book.category IN (SELECT value FROM json_each(:cats))) "
    "  AND (:book = '' OR book.title = :book) "
    "  AND (:volume = 0 OR book.volume = :volume)"
)
_SCAN_CAP: Final[int] = 50_000
_COUNT_UNFILTERED = "SELECT count(*) FROM (SELECT 1 FROM pages WHERE pages MATCH :q LIMIT :cap)"
_COUNT_FILTERED = "SELECT count(*) FROM (SELECT 1 " + _FILTER + " LIMIT :cap)"  # noqa: S608
_SEARCH = (
    "SELECT pages.urn AS urn, pages.page AS page, pages.content AS content "
    + _FILTER
    + " ORDER BY pages.rowid LIMIT :limit OFFSET :offset"
)
_FACET_CATEGORIES = (
    "SELECT book.category AS category, count(*) AS n FROM ("
    "SELECT pages.urn AS urn FROM pages WHERE pages MATCH :q LIMIT :cap"
    ") m JOIN book ON book.urn = m.urn GROUP BY book.category ORDER BY n DESC"
)
_FACET_BOOKS = (
    "SELECT book.title AS title, count(*) AS n "
    "FROM pages JOIN book ON book.urn = pages.urn "
    "WHERE pages MATCH :q "
    "  AND (:cats = '' OR book.category IN (SELECT value FROM json_each(:cats))) "
    "GROUP BY book.title ORDER BY n DESC"
)
_FACET_VOLUMES = (
    "SELECT book.volume AS volume, count(*) AS n "
    "FROM pages JOIN book ON book.urn = pages.urn "
    "WHERE pages MATCH :q "
    "  AND (:cats = '' OR book.category IN (SELECT value FROM json_each(:cats))) "
    "  AND (:book = '' OR book.title = :book) AND book.volume IS NOT NULL "
    "GROUP BY book.volume ORDER BY book.volume"
)


def _connect() -> sqlite3.Connection:
    """Open the corpus index read-only via the shared artifact opener."""
    return open_ro_db(
        ARTIFACT__CORPUS_DB,
        "Corpus index not built; run scripts/build_corpus_index.py to materialize it",
    )


@lru_cache(maxsize=1)
def _meta() -> dict[str, Book]:
    """Map every catalog URN to its Book, for result display: title, author,
    category, and volume all come from the one catalog projection."""
    books, _ = books_repo.list_books()
    return {b.urn: b for b in books}


@lru_cache(maxsize=1)
def _title_en_by_ar() -> dict[str, str | None]:
    """Map each Arabic book title (the book facet's key) to its English title,
    so the book filter can read in English while still filtering by the key."""
    return {b.title_ar: b.title_en for b in _meta().values()}


def search_windows(q: str, mode: SearchMode) -> list[str]:
    """Fold the query and return the phrase windows to match + locate. ``exact``
    -> one window (the whole phrase). ``broad`` -> overlapping ``_BROAD_WINDOW``
    word windows when the query is longer than one window, else the whole
    phrase. Empty query -> ``[]``. Shared by the corpus-wide FTS search and the
    in-book page scan — the one place a query becomes match windows.

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


def _match_expr(windows: list[str]) -> str:
    """Join folded phrase windows into one FTS5 OR-of-phrases MATCH expression."""
    return " OR ".join(f'"{w}"' for w in windows)


def locate_snippet(content: str, windows: list[str]) -> tuple[bool, str]:
    """Locate the first folded ``windows`` hit in ``content`` and return
    ``(found, snippet)`` — a fold-aware excerpt keeping original orthography, or
    ``(False, head)`` when no window is present. The one place the fold-aware
    snippet is built; shared by the corpus-wide FTS path and the in-book scan.

    Uses ``patterns.fold_with_offsets`` for the folded→original index map; the
    match ends after the last folded letter (``origin[hit + len - 1] + 1``), so
    the trailing sentinel that map carries is never indexed here."""
    folded, origin = fold_with_offsets(content)
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


def _category_set(categories: tuple[str, ...]) -> str:
    """The bound ``:cats`` value: the selected category slugs as a sorted,
    deduplicated JSON array, or ``''`` for no category constraint. The API
    layer rejects unknown slugs before this runs."""
    if not categories:
        return ""
    return json.dumps(sorted(set(categories)))


def search(
    query: SearchQuery,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[CorpusMatch], int]:
    """Return ``(slice, total)`` of corpus pages matching ``query`` + filters.

    Cross-corpus FTS5 search. Results come back in index (rowid) order, paginated
    directly by the FTS engine — not bm25-ranked, because ranking scores the
    whole match set and is pathologically slow for common terms. A common single
    word matches millions of pages and counting every one took 30-40s, so counts
    are bounded by ``_SCAN_CAP`` (exact below it, a floor at/above it); the count
    joins ``book`` only when a category/book/volume filter is set, so an
    unfiltered count stays cheap for common terms. In-book search is a separate
    path (``search_in_book``): a single book is scanned in memory, since FTS
    scoped by urn walks the whole posting list for late books.
    """
    windows = search_windows(query.q, query.mode)
    if not windows:
        return [], 0
    con = _connect()
    params: dict[str, Any] = {
        "q": _match_expr(windows),
        "cats": _category_set(query.categories),
        "book": query.book,
        "volume": query.volume,
        "limit": limit,
        "offset": offset,
        "cap": _SCAN_CAP,
    }
    if params["cats"] or query.book or query.volume:
        total = int(con.execute(_COUNT_FILTERED, params).fetchone()[0])
    else:
        count_params: dict[str, Any] = {"q": params["q"], "cap": _SCAN_CAP}
        total = int(con.execute(_COUNT_UNFILTERED, count_params).fetchone()[0])
    rows = con.execute(_SEARCH, params).fetchall()
    meta = _meta()
    matches: list[CorpusMatch] = []
    uncatalogued: set[str] = set()
    for row in rows:
        urn = row["urn"]
        b = meta.get(urn)
        if b is None:
            uncatalogued.add(urn)
        _, snippet = locate_snippet(row["content"], windows)
        matches.append(
            CorpusMatch(
                urn=urn,
                title_ar=b.title_ar if b else urn,
                title_en=b.title_en if b else None,
                author=b.author if b else None,
                category=b.category if b else "",
                volume=b.volume if b else None,
                page=int(row["page"]),
                snippet=snippet,
            )
        )
    if uncatalogued:
        _logger.warning(
            "corpus-match-uncatalogued",
            count=len(uncatalogued),
            urns=sorted(uncatalogued),
        )
    return matches, total


def facets(
    q: str = "",
    mode: SearchMode = "exact",
    categories: tuple[str, ...] = (),
    book: str = "",
) -> SearchFacets:
    """Drill-down facets for the active match mode: categories (over q, always
    the query-global distribution), books (within the selected category set),
    volumes (within the chosen book). Each scoped level is computed only when
    its parent filter is set, so the menus stay scoped and small.

    When the category scan fills ``_SCAN_CAP`` the match-set exceeds the cap, so
    the partial split is biased toward the first books scanned; the facets are
    dropped rather than showing a wrong breakdown, since drill-down is moot at
    that scale and the result count already reads as capped.
    """
    windows = search_windows(q, mode)
    if not windows:
        return SearchFacets(categories=[], books=[], volumes=[])
    expr = _match_expr(windows)
    cats = _category_set(categories)
    con = _connect()
    cat_rows = con.execute(_FACET_CATEGORIES, {"q": expr, "cap": _SCAN_CAP}).fetchall()
    if sum(int(r["n"]) for r in cat_rows) >= _SCAN_CAP:
        return SearchFacets(categories=[], books=[], volumes=[])
    book_rows = con.execute(_FACET_BOOKS, {"q": expr, "cats": cats}).fetchall() if cats else []
    vol_rows = (
        con.execute(_FACET_VOLUMES, {"q": expr, "cats": cats, "book": book}).fetchall()
        if book
        else []
    )
    en_by_ar = _title_en_by_ar()
    return SearchFacets(
        categories=[
            CategoryFacet(slug=r["category"], count=int(r["n"])) for r in cat_rows if r["category"]
        ],
        books=[
            BookFacet(title=r["title"], title_en=en_by_ar.get(r["title"]), count=int(r["n"]))
            for r in book_rows
            if r["title"]
        ],
        volumes=[VolumeFacet(volume=int(r["volume"]), count=int(r["n"])) for r in vol_rows],
    )


def search_in_book(
    book_urn: str,
    q: str,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[BookSearchMatch], int]:
    """Return ``(slice, total)`` of pages in ``book_urn`` whose folded text
    contains a folded query window, each with a fold-aware snippet.

    Scans the book's own pages in memory (via ``reader.page_rows``, the page
    SSOT) rather than the global FTS index: a single book is small enough to
    scan, and FTS scoped by urn walks the whole posting list for common terms in
    late-indexed books. Shares ``search_windows`` + ``locate_snippet`` with the
    corpus-wide path — the fold + snippet logic lives once.
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
