"""MCP server exposing sol-next2's book corpus as Model Context Protocol tools.

This is a standalone stdio server. It does **not** import the FastAPI app; it
calls the running backend over HTTP — the same talk-to-the-backend-over-HTTP
contract the frontend follows. Three design choices worth noting:

  * Tool descriptions are written as *deterministic selectors* — the prose is
    what makes Claude pick the right tool, so each states when to use it.
  * Upstream failures surface as a single structured error type
    (``CorpusError``); nothing is swallowed or replaced by an empty stand-in.
  * Tool handlers are module-private (``_``-prefixed) and registered via
    ``mcp.add_tool`` (the one registration style) with the public tool name set
    explicitly — they are MCP tools, not importable Python API (DRY-001).
"""

from __future__ import annotations

from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from backend.core.constants import HTTP__DEFAULT_PAGE_SIZE, HTTP__REQUEST_TIMEOUT_SECONDS
from backend.core.http import status

# The local FastAPI backend this server proxies. A module constant (not an env
# read) so CENTRAL-001 stays satisfied and this server carries no dependency on
# the backend's required SOL_BOOKS_DIR setting.
_API_BASE_URL = "http://127.0.0.1:8001/api"

mcp = FastMCP("sol-next2-corpus")


class CorpusError(RuntimeError):
    """An upstream backend call failed. Surfaced to the caller, never swallowed."""


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET a backend path and return parsed JSON, or raise a structured error.

    ``None``-valued params are dropped rather than sent as empty strings — an
    empty ``category=`` would otherwise filter the catalog down to nothing.
    """
    query = {key: value for key, value in (params or {}).items() if value is not None}
    try:
        with httpx.Client(base_url=_API_BASE_URL, timeout=HTTP__REQUEST_TIMEOUT_SECONDS) as client:
            response = client.get(path, params=query)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == status.HTTP_404_NOT_FOUND:
            raise CorpusError(f"Not found: {path}") from exc
        raise CorpusError(f"Backend returned {exc.response.status_code} for {path}") from exc
    except httpx.HTTPError as exc:
        raise CorpusError(f"Backend unreachable at {_API_BASE_URL}: {exc!s}") from exc


def _list_books(
    category: str | None = None,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> Any:
    """List books in the corpus. Use to browse or page the catalog.

    `category` filters by a taxonomy slug (omit for all categories). `limit`
    caps the page size and `offset` skips records — both validated by the
    backend, which returns a structured error if out of range. Returns a page
    envelope: ``{items: [...], total, limit, offset}``.
    """
    return _get("/books", {"category": category, "limit": limit, "offset": offset})


def _get_book(urn: str) -> Any:
    """Fetch one book's full record by its URN (stable id). Raises if absent."""
    return _get(f"/books/{urn}")


def _get_table_of_contents(book_urn: str) -> Any:
    """Get the table of contents (chapter/section tree) for a book, by its URN."""
    return _get(f"/books/{book_urn}/toc")


def _get_page(book_urn: str, page_number: int) -> Any:
    """Get the content of a single page of a book. `page_number` is 1-based.

    Raises a structured error if the book or page does not exist — it never
    returns an empty page as a stand-in.
    """
    return _get(f"/books/{book_urn}/pages/{page_number}")


def _daily_picks() -> Any:
    """Return today's curated daily picks (the Daily Pair / Verse / Hadith set)."""
    return _get("/daily")


def _search(
    q: str,
    mode: str = "exact",
    category: str | None = None,
    book: str | None = None,
    volume: int | None = None,
    limit: int = HTTP__DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> Any:
    """Full-text search across ALL book content — the fast way to find where a
    word or phrase occurs across the corpus (diacritic- + letter-variant-
    insensitive, backed by the FTS5 index). Use this to locate passages, not to
    browse the catalog.

    `q` is the Arabic phrase (folded before matching). `mode` is 'exact' (whole
    phrase) or 'broad' (overlapping sub-phrases; looser, more hits). Narrow with
    `category` (slug), `book` (title), `volume`. Returns a page of matches:
    ``{items: [{urn, title_ar, title_en, author, category, volume, page, snippet}],
    total, limit, offset}``."""
    return _get(
        "/search",
        {
            "q": q,
            "mode": mode,
            "category": category,
            "book": book,
            "volume": volume,
            "limit": limit,
            "offset": offset,
        },
    )


def _search_in_book(
    book_urn: str, q: str, limit: int = HTTP__DEFAULT_PAGE_SIZE, offset: int = 0
) -> Any:
    """Full-text search WITHIN one book's pages (by URN). Use when you already
    know the book and want its matching pages + snippets. Returns ``{items:
    [{page, snippet}], total, limit, offset}``."""
    return _get(f"/books/{book_urn}/search", {"q": q, "limit": limit, "offset": offset})


def _search_quran(q: str, limit: int = HTTP__DEFAULT_PAGE_SIZE, offset: int = 0) -> Any:
    """Search the Qurʾān for verses containing an Arabic term or phrase (folded).
    Returns a page of ayat: ``{items: [{surah, ayah, verse_count, text_ar,
    text_plain, text_en}], total, limit, offset}``."""
    return _get("/quran/search", {"q": q, "limit": limit, "offset": offset})


mcp.add_tool(_list_books, name="list_books")
mcp.add_tool(_get_book, name="get_book")
mcp.add_tool(_get_table_of_contents, name="get_table_of_contents")
mcp.add_tool(_get_page, name="get_page")
mcp.add_tool(_daily_picks, name="daily_picks")
mcp.add_tool(_search, name="search")
mcp.add_tool(_search_in_book, name="search_in_book")
mcp.add_tool(_search_quran, name="search_quran")


def main() -> None:
    """Run the server over stdio — the transport an MCP client (Claude Code) spawns."""
    mcp.run()


if __name__ == "__main__":
    main()
