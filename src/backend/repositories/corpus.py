"""Repository for the corpus full-text index — backed by ``data/corpus.db``.

All SQL for cross-corpus content search lives here (CENTRAL-005). The FTS5 index
stores each page TWICE: a ``fold`` column (the text put through
``patterns.fold_search`` — diacritics + annotation signs removed and the
alef/yaa/taa letter variants folded) which is the matched column, and an
UNINDEXED ``content`` column holding the original text for display. The query is
folded the same way, so a search is insensitive to diacritics AND letter-variant
spelling; snippets are then built from the original ``content`` (fold-aware), so
results keep true manuscript orthography. A small ``book(urn, category, title,
volume)`` table (joined by URN) backs the category -> book -> volume filters.
Two match modes: ``exact`` (the whole phrase) and ``broad`` (OR of the query's
overlapping fixed-width word windows — finds sub-phrases; a 4-word window stays
distinctive so even a long, common-worded verse resolves in well under a second).
``scripts/build_corpus_index.py`` writes it (no FTS ``optimize`` pass); opened
read-only + immutable at serve.
"""

from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

from backend.core.constants import (
    CORPUS__SNIPPET_HEAD_CHARS,
    CORPUS__SNIPPET_WINDOW_CHARS,
    HTTP__DEFAULT_PAGE_SIZE,
)
from backend.core.logging import get_logger
from backend.models.book import Book
from backend.models.search import BookFacet, CategoryFacet, CorpusMatch, SearchFacets, VolumeFacet
from backend.patterns import fold_search
from backend.repositories import books as books_repo
from backend.repositories._data_loader import open_ro_db

_logger = get_logger("shia-library.corpus")

_DB_FILE = "corpus.db"
_BROAD = "broad"
# Width of the overlapping word window OR-ed together in broad mode. Four
# consecutive words stay distinctive enough that even a long, common-worded
# verse matches only a few hundred pages (a 2-word window matched millions).
_BROAD_WINDOW: Final[int] = 4

CORPUS_SCHEMA: str = """
CREATE VIRTUAL TABLE pages USING fts5(
  fold,
  content UNINDEXED,
  urn UNINDEXED,
  page UNINDEXED,
  tokenize = 'unicode61 remove_diacritics 2'
);
"""

BOOK_SCHEMA: str = """
DROP TABLE IF EXISTS book;
CREATE TABLE book (
  urn      TEXT PRIMARY KEY,
  category TEXT NOT NULL DEFAULT '',
  title    TEXT NOT NULL DEFAULT '',
  volume   INTEGER
);
CREATE INDEX idx_book_category ON book (category);
CREATE INDEX idx_book_title ON book (title);
"""

_INSERT = "INSERT INTO pages (fold, content, urn, page) VALUES (:fold, :content, :urn, :page)"
_BOOK_INSERT = (
    "INSERT OR REPLACE INTO book (urn, category, title, volume) "
    "VALUES (:urn, :category, :title, :volume)"
)

_FILTER = (
    "FROM pages JOIN book ON book.urn = pages.urn "
    "WHERE pages MATCH :q "
    "  AND (:urn = '' OR pages.urn = :urn) "
    "  AND (:category = '' OR book.category = :category) "
    "  AND (:book = '' OR book.title = :book) "
    "  AND (:volume = 0 OR book.volume = :volume)"
)
# A common single word matches millions of pages, and counting / ranking /
# faceting every one took 30-40s. Cap the FTS rows any one query examines:
# below the cap the count is exact and the whole match-set is ranked; at it the
# total is a floor and the (now partial, book-biased) facet split is dropped.
_SCAN_CAP: Final[int] = 50_000
# S608 is a false positive on the two bounded queries below: each is built from
# the constant _FILTER and run with bound parameters (:q, :cap, :limit), never
# from interpolated input — the same construction the unbounded originals used.
_COUNT = "SELECT count(*) FROM (SELECT 1 " + _FILTER + " LIMIT :cap)"  # noqa: S608
_SEARCH = (
    "SELECT urn, page, content FROM ("  # noqa: S608
    "SELECT pages.urn AS urn, pages.page AS page, pages.content AS content, rank AS r "
    + _FILTER
    + " LIMIT :cap) ORDER BY r LIMIT :limit OFFSET :offset"
)
_FACET_CATEGORIES = (
    "SELECT book.category AS category, count(*) AS n FROM ("
    "SELECT pages.urn AS urn FROM pages WHERE pages MATCH :q LIMIT :cap"
    ") m JOIN book ON book.urn = m.urn GROUP BY book.category ORDER BY n DESC"
)
_FACET_BOOKS = (
    "SELECT book.title AS title, count(*) AS n "
    "FROM pages JOIN book ON book.urn = pages.urn "
    "WHERE pages MATCH :q AND (:category = '' OR book.category = :category) "
    "GROUP BY book.title ORDER BY n DESC"
)
_FACET_VOLUMES = (
    "SELECT book.volume AS volume, count(*) AS n "
    "FROM pages JOIN book ON book.urn = pages.urn "
    "WHERE pages MATCH :q AND (:category = '' OR book.category = :category) "
    "  AND (:book = '' OR book.title = :book) AND book.volume IS NOT NULL "
    "GROUP BY book.volume ORDER BY book.volume"
)


def create_index(out: Path) -> sqlite3.Connection:
    """Create a fresh corpus index at ``out`` and apply the FTS schema."""
    if out.exists():
        out.unlink()
    con = sqlite3.connect(out)
    con.executescript(CORPUS_SCHEMA)
    return con


def insert_pages(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """Insert projected page rows (``fold``/``content``/``urn``/``page``)."""
    con.executemany(_INSERT, rows)


def book_table_rows(books: list[Book]) -> list[dict[str, Any]]:
    """Project catalog books into ``book`` filter-table rows — the single source
    of the URN -> (category, title, volume) projection, shared by the index
    builder and the book-table re-migration script."""
    return [
        {"urn": b.urn, "category": b.category, "title": b.title_ar, "volume": b.volume}
        for b in books
    ]


def build_book_table(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    """(Re)create + populate the URN -> (category, title, volume) filter table."""
    con.executescript(BOOK_SCHEMA)
    con.executemany(_BOOK_INSERT, rows)


def _connect() -> sqlite3.Connection:
    """Open the corpus index read-only via the shared artifact opener."""
    return open_ro_db(
        _DB_FILE, "Corpus index not built; run scripts/build_corpus_index.py to materialize it"
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


def _fold_windows(q: str, mode: str) -> list[str]:
    """Fold the query and return the phrase windows to match + locate. ``exact``
    -> one window (the whole phrase). ``broad`` -> overlapping ``_BROAD_WINDOW``
    word windows when the query is longer than one window, else the whole
    phrase. Empty query -> ``[]``."""
    words = [w for w in fold_search(q).replace('"', " ").split() if w]
    if not words:
        return []
    if mode == _BROAD and len(words) > _BROAD_WINDOW:
        return [
            " ".join(words[i : i + _BROAD_WINDOW]) for i in range(len(words) - _BROAD_WINDOW + 1)
        ]
    return [" ".join(words)]


def _match_expr(windows: list[str]) -> str:
    """Join folded phrase windows into one FTS5 OR-of-phrases MATCH expression."""
    return " OR ".join(f'"{w}"' for w in windows)


def _fold_with_map(text: str) -> tuple[str, list[int]]:
    """Fold ``text`` for matching while recording, for each folded character,
    the index of the original character it came from. Folding drops marks and
    1:1-replaces letters, so each folded position maps to exactly one original
    position — enough to slice an excerpt of the original around a folded hit."""
    folded: list[str] = []
    origin: list[int] = []
    for i, ch in enumerate(text):
        f = fold_search(ch)
        if f:
            folded.append(f)
            origin.append(i)
    return "".join(folded), origin


def _snippet(content: str, windows: list[str]) -> str:
    """Excerpt the original ``content`` around the first folded ``windows`` hit,
    keeping original orthography. Falls to the head only if no window is located
    (the row matched, so a window is normally present)."""
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
        return f"{prefix}{content[left:right]}{suffix}"
    head = content[:CORPUS__SNIPPET_HEAD_CHARS]
    return f"{head}…" if len(content) > CORPUS__SNIPPET_HEAD_CHARS else head


def search(
    q: str = "",
    mode: str = "exact",
    urn: str = "",
    category: str = "",
    book: str = "",
    volume: int = 0,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[CorpusMatch], int]:
    """Return ``(slice, total)`` of corpus pages matching ``q`` (mode) + filters.

    ``urn`` restricts the search to a single book; it is the one engine that
    backs both the cross-corpus search and the reader's in-book search."""
    windows = _fold_windows(q, mode)
    if not windows:
        return [], 0
    con = _connect()
    params: dict[str, Any] = {
        "q": _match_expr(windows),
        "urn": urn,
        "category": category,
        "book": book,
        "volume": volume,
        "limit": limit,
        "offset": offset,
        "cap": _SCAN_CAP,
    }
    # Bounded count: exact below the cap, reported as the cap (a floor) above it.
    total = int(con.execute(_COUNT, params).fetchone()[0])
    rows = con.execute(_SEARCH, params).fetchall()
    meta = _meta()
    matches: list[CorpusMatch] = []
    uncatalogued: set[str] = set()
    for row in rows:
        urn = row["urn"]
        b = meta.get(urn)
        if b is None:
            uncatalogued.add(urn)
        matches.append(
            CorpusMatch(
                urn=urn,
                title_ar=b.title_ar if b else urn,
                title_en=b.title_en if b else None,
                author=b.author if b else None,
                category=b.category if b else "",
                volume=b.volume if b else None,
                page=int(row["page"]),
                snippet=_snippet(row["content"], windows),
            )
        )
    if uncatalogued:
        # The index holds pages whose URN is no longer in the catalog (e.g. a book
        # removed after the index was built). Surface it loudly so the URN-as-title
        # display can never quietly mask a stale index.
        _logger.warning(
            "corpus-match-uncatalogued",
            count=len(uncatalogued),
            urns=sorted(uncatalogued),
        )
    return matches, total


def facets(q: str = "", mode: str = "exact", category: str = "", book: str = "") -> SearchFacets:
    """Drill-down facets for the active match mode: categories (over q), books
    (within category), volumes (within the chosen book). Each level is computed
    only when its parent filter is set, so the menus stay scoped and small."""
    windows = _fold_windows(q, mode)
    if not windows:
        return SearchFacets(categories=[], books=[], volumes=[])
    expr = _match_expr(windows)
    con = _connect()
    cat_rows = con.execute(_FACET_CATEGORIES, {"q": expr, "cap": _SCAN_CAP}).fetchall()
    # A filled scan means the match-set exceeds the cap, so this partial split is
    # biased toward the first books scanned — drop facets rather than show a wrong
    # breakdown (drill-down is moot at that scale, and the result count says "cap").
    if sum(int(r["n"]) for r in cat_rows) >= _SCAN_CAP:
        return SearchFacets(categories=[], books=[], volumes=[])
    book_rows = (
        con.execute(_FACET_BOOKS, {"q": expr, "category": category}).fetchall() if category else []
    )
    vol_rows = (
        con.execute(_FACET_VOLUMES, {"q": expr, "category": category, "book": book}).fetchall()
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
