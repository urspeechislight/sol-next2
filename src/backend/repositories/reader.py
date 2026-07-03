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
from typing import Any, NamedTuple, cast

from backend.core.constants import READER__SOURCE_CACHE_MAX
from backend.core.errors import ResourceNotFoundError
from backend.core.logging import get_logger
from backend.models.reader import BookPage, Toc, TocEntry
from backend.repositories import books as books_repo
from backend.repositories import manuscript as manuscript_repo

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
    return cast(dict[str, Any], doc)


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
    content_dict = cast(dict[str, Any], content_raw)
    book_key = _first_book_key(content_dict)
    if book_key is None:
        return []
    rows = content_dict.get(book_key)
    if not isinstance(rows, list):
        raise ReaderSourceError("source 'content' rows are not a list")
    return cast(list[Any], rows)


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
        row_dict = cast(dict[str, Any], row)
        page = row_dict.get("page_number")
        body = (row_dict.get("content") or "").strip()
        if not body:
            continue
        if not isinstance(page, int) or page < 1:
            _logger.error("page-row-corrupt", urn=book_urn, page_number=repr(page))
            raise ReaderSourceError(
                f"Corrupt page in {book_urn}: content present but page_number is {page!r}"
            )
        rows.append(PageRow(page=page, content=body))
    return rows


def try_get_toc(book_urn: str) -> Toc | None:
    """Return the TOC for ``book_urn``, or None when the book has no TOC section.

    None is the explicit absent-TOC signal so call sites model absence without a
    try/except. Present-but-corrupt TOC (rows not a list) still raises
    ReaderSourceError — that is corruption, not absence.
    """
    src = books_repo.source_path(book_urn)
    if src is None:
        return None
    doc = _load_source(src)
    toc_raw = doc.get("toc")
    if not isinstance(toc_raw, dict):
        return None
    toc_dict = cast(dict[str, Any], toc_raw)
    book_key = _first_book_key(toc_dict)
    if book_key is None:
        return None
    rows = toc_dict.get(book_key)
    if not isinstance(rows, list):
        raise ReaderSourceError("source 'toc' rows are not a list")
    entries = _toc_entries_from_rows(book_urn, cast(list[Any], rows))
    return Toc(book_urn=book_urn, entries=entries)


def get_toc(book_urn: str) -> Toc:
    """Return the TOC for ``book_urn`` or raise ResourceNotFoundError."""
    toc = try_get_toc(book_urn)
    if toc is None:
        raise ResourceNotFoundError(kind="toc", identifier=book_urn)
    return toc


def _toc_entries_from_rows(book_urn: str, rows: list[Any]) -> list[TocEntry]:
    """Shape validated toc rows into TocEntry objects, skipping malformed ones."""
    entries: list[TocEntry] = []
    for row in rows:
        if not isinstance(row, dict):
            _logger.warning("toc-row-skipped", urn=book_urn, reason="not-a-mapping")
            continue
        row_dict = cast(dict[str, Any], row)
        page_num = row_dict.get("page_number")
        title = (row_dict.get("title") or "").strip()
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
    return entries


def get_page(book_urn: str, page_number: int) -> BookPage:
    """Return the requested page or raise ``ResourceNotFoundError``.

    Structured ``hadiths`` (isnad + matn + narrators) come from the manuscript
    index built by Phase 3 extract, via ``manuscript.hadiths_for_page``. When the
    page has parsed hadiths they are served and ``text_ar`` is ``None`` (the two
    are mutually exclusive per the ``BookPage`` contract); otherwise ``text_ar``
    carries the raw page text honestly — for prose pages, or before the index is
    built. ``text_en`` is the single wiring point for an English rendering: the
    corpus has no English column yet, so it stays ``None`` and the reader shows a
    labelled preview; set it here the moment translations land.
    """
    rows = page_rows(book_urn)
    if not rows:
        raise ResourceNotFoundError(kind="page", identifier=f"{book_urn}#{page_number}")
    match = next((r for r in rows if r.page == page_number), None)
    if match is None:
        raise ResourceNotFoundError(kind="page", identifier=f"{book_urn}#{page_number}")
    hadiths = manuscript_repo.hadiths_for_page(book_urn, page_number)
    return BookPage(
        page_number=page_number,
        total_pages=len(rows),
        chapter_title=_chapter_title_at(book_urn, page_number),
        chapter_title_en=None,
        section_title="",
        section_title_en=None,
        hadiths=hadiths,
        text_ar=None if hadiths else match.content,
        text_en=None,
    )


def _chapter_title_at(book_urn: str, page_number: int) -> str:
    """Chapter title for ``page_number``: the latest TOC entry whose page is
    at most ``page_number``, or ``""`` for a book with no TOC section.

    Consumes the same ``try_get_toc`` parse as the TOC endpoint, so there is
    exactly one reading of the raw TOC rows. A corrupt TOC therefore raises
    ``ReaderSourceError`` here exactly as it does there: wrong is worse than
    absent, and a source file with a broken TOC section needs fixing, not
    masking behind an empty title.
    """
    toc = try_get_toc(book_urn)
    if toc is None:
        return ""
    current = ""
    for entry in toc.entries:
        if entry.page <= page_number:
            current = entry.title
    return current
