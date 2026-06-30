"""Reader repository — loads TOC + page content lazily from corpus source files.

For each requested URN we look up the source file path via
``books.source_path(urn)``, open the source JSON, and shape its
``toc`` / ``content`` blocks into our Pydantic ``Toc`` / ``BookPage``
models. Source-file reads are cached per (urn, page_number).

Rich fields (parsed isnad, narrators, English matn, cross-refs, grades)
are **not populated** for corpus-sourced books — the source files don't
include them. They will be populated once the upstream ingest pipeline
emits them; see ``docs/adr/0001-storage-contract.md``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, NamedTuple

from backend.core.constants import READER__SOURCE_CACHE_MAX
from backend.core.errors import ResourceNotFoundError
from backend.core.logging import get_logger
from backend.models.reader import BookPage, Hadith, Toc, TocEntry
from backend.repositories import books as books_repo

_logger = get_logger("shia-library.reader")


class ReaderSourceError(RuntimeError):
    """The source file for a URN exists in the index but cannot be opened."""


@lru_cache(maxsize=READER__SOURCE_CACHE_MAX)
def _load_source(path: Path) -> dict[str, Any]:
    """Open and JSON-parse one source book file. Cached for hot books."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        _logger.error("source-read-failed", path=str(path), exc_info=True)
        raise ReaderSourceError(f"Cannot read corpus source at {path}") from exc
    if not isinstance(doc, dict):
        _logger.error("source-not-object", path=str(path))
        raise ReaderSourceError(f"Source at {path} is not a JSON object")
    return doc


def _first_book_key(d: dict[str, Any]) -> str | None:
    """The TOC/content dicts are keyed by a single numeric book_id — return it.

    Each source file holds exactly one book; more than one key is source
    corruption, raised loudly rather than silently dropping the extra books.
    """
    keys = list(d.keys())
    if len(keys) > 1:
        raise ReaderSourceError(f"source maps {len(keys)} books in one file, expected one")
    return keys[0] if keys else None


def _content_rows(doc: dict[str, Any]) -> list[Any]:
    """Return the page-content rows for a source document.

    An absent ``content`` section yields ``[]`` (a legitimately page-less
    book); a present-but-malformed one — wrong types — raises
    ``ReaderSourceError`` instead of masquerading as page-less and 404-ing.
    """
    content_raw = doc.get("content")
    if content_raw is None:
        return []
    if not isinstance(content_raw, dict):
        raise ReaderSourceError("source 'content' is not an object")
    book_key = _first_book_key(content_raw)
    if book_key is None:
        return []
    rows = content_raw.get(book_key)
    if not isinstance(rows, list):
        raise ReaderSourceError("source 'content' rows are not a list")
    return rows


class PageRow(NamedTuple):
    """One validated (page number, content) row from a book's source file."""

    page: int
    content: str


def _require_source(book_urn: str, kind: str) -> Path:
    """Resolve a book's source file path or raise ``ResourceNotFoundError(kind)``.
    The one place the source-path lookup + not-found raise lives."""
    src = books_repo.source_path(book_urn)
    if src is None:
        raise ResourceNotFoundError(kind=kind, identifier=book_urn)
    return src


def page_rows(book_urn: str) -> list[PageRow]:
    """The single source of a book's (page, content) rows: load the source file
    and return its validated content rows in source order. Raises
    ``ResourceNotFoundError`` when the book has no source file. Consumed by
    ``get_page`` and the corpus index builder so the page extraction lives once.
    """
    src = _require_source(book_urn, "book")
    rows: list[PageRow] = []
    for row in _content_rows(_load_source(src)):
        if not isinstance(row, dict):
            _logger.warning("page-row-skipped", urn=book_urn, reason="not-a-mapping")
            continue
        page = row.get("page_number")
        body = (row.get("content") or "").strip()
        if not body:
            continue
        if not isinstance(page, int) or page < 1:
            _logger.error("page-row-corrupt", urn=book_urn, page_number=repr(page))
            raise ReaderSourceError(
                f"Corrupt page in {book_urn}: content present but page_number is {page!r}"
            )
        rows.append(PageRow(page=page, content=body))
    return rows


def get_toc(book_urn: str) -> Toc:
    """Return the TOC for ``book_urn`` or raise ResourceNotFoundError."""
    src = _require_source(book_urn, "toc")
    doc = _load_source(src)
    toc_raw = doc.get("toc")
    if not isinstance(toc_raw, dict):
        raise ResourceNotFoundError(kind="toc", identifier=book_urn)
    book_key = _first_book_key(toc_raw)
    if book_key is None:
        raise ResourceNotFoundError(kind="toc", identifier=book_urn)
    rows = toc_raw.get(book_key)
    if not isinstance(rows, list):
        raise ReaderSourceError("source 'toc' rows are not a list")
    entries: list[TocEntry] = []
    for row in rows:
        if not isinstance(row, dict):
            _logger.warning("toc-row-skipped", urn=book_urn, reason="not-a-mapping")
            continue
        page_num = row.get("page_number")
        title = (row.get("title") or "").strip()
        if not title:
            continue
        if not isinstance(page_num, int) or page_num < 1:
            _logger.warning(
                "toc-row-skipped",
                urn=book_urn,
                reason="bad-page-number",
                page_number=repr(page_num),
                title=title,
            )
            continue
        entries.append(TocEntry(page=page_num, title=title))
    return Toc(book_urn=book_urn, entries=entries)


def get_page(book_urn: str, page_number: int) -> BookPage:
    """Return the requested page or raise ResourceNotFoundError."""
    rows = page_rows(book_urn)
    if not rows:
        raise ResourceNotFoundError(kind="page", identifier=f"{book_urn}#{page_number}")
    match = next((r for r in rows if r.page == page_number), None)
    if match is None:
        raise ResourceNotFoundError(kind="page", identifier=f"{book_urn}#{page_number}")
    return BookPage(
        page_number=page_number,
        total_pages=len(rows),
        chapter_title=_chapter_title_at(book_urn, page_number),
        chapter_title_en=None,
        section_title="",
        section_title_en=None,
        hadiths=[
            Hadith(
                n=1,
                isnad_ar="",
                matn_ar=match.content,
                matn_en=None,
                narrators=[],
                grade=None,
                cross_refs=[],
            )
        ],
    )


def _chapter_title_at(book_urn: str, page_number: int) -> str:
    """Best-effort chapter title for ``page_number`` — the latest TOC entry
    whose page <= page_number. Best-effort by design: an absent or malformed
    TOC yields an empty title rather than failing the page load. The loud TOC
    validation lives in ``get_toc``.
    """
    src = books_repo.source_path(book_urn)
    if src is None:
        return ""
    toc_raw = _load_source(src).get("toc")
    if not isinstance(toc_raw, dict) or not toc_raw:
        return ""
    rows = next(iter(toc_raw.values()))
    if not isinstance(rows, list):
        return ""
    current = ""
    for row in rows:
        if not isinstance(row, dict):
            continue
        rp = row.get("page_number")
        if isinstance(rp, int) and rp <= page_number:
            current = (row.get("title") or "").strip()
    return current
