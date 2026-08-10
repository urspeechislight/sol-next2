"""Reader repository: TOC from corpus source files, page text proxied from the
consolidated backend.

The TOC stays a local concern. The synthesized override index plus the scraped
source-file TOC shape into the Pydantic ``Toc`` / ``TocEntry`` models. Page
text, the page count, and the footnote block come from the one consolidated
backend that owns the page index (``/api/r/page/{urn}/{n}``), so a book added
there is immediately readable here with no local rebuild. The manuscript extract
of structured hadiths stays a local overlay, composed onto the proxied text in
``get_page``. A page's ``footnote`` block is split into the apparatus by the one
canonical splitter in ``backend.pipeline.text``.

``page_rows`` remains the local page accessor that the in-book scan
(``corpus.search_in_book``) reads; it is no longer the page-text source for
``get_page``. Rich fields (parsed isnad, narrators, English matn, cross-refs,
grades) are **not populated** for corpus-sourced books, because the backend page
carries raw text only. They will be populated once the upstream ingest pipeline
emits them; see ``docs/adr/0001-storage-contract.md``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, NamedTuple, cast

import httpx

from backend.core.constants import (
    ARTIFACT__TOC_INDEX,
    HTTP__REQUEST_TIMEOUT_SECONDS,
    READER__SOURCE_CACHE_MAX,
)
from backend.core.errors import ResourceNotFoundError
from backend.core.logging import get_logger
from backend.core.paths import data_path
from backend.core.settings import get_settings
from backend.models.reader import BookPage, Footnote, Toc, TocEntry
from backend.pipeline.text import split_footnote_block
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
    """One validated (page number, content, footnote block) row from a book's
    source file. ``footnote`` is the raw combined block as digitized, or None
    when the page prints no notes."""

    page: int
    content: str
    footnote: str | None = None


def _require_source(book_urn: str, kind: str) -> Path:
    """Resolve a book's source file path or raise ``ResourceNotFoundError(kind)``.
    The one place the source-path lookup + not-found raise lives."""
    src = books_repo.source_path(book_urn)
    if src is None:
        raise ResourceNotFoundError(kind=kind, identifier=book_urn)
    return src


def _row_footnote(book_urn: str, page: int, row_dict: dict[str, Any]) -> str | None:
    """Validate and normalize one row's raw footnote block.

    A non-string, non-null value is source corruption and raises loudly
    (wrong is worse than absent); a blank block normalizes to None, the
    explicit no-notes signal.
    """
    fn_raw = row_dict.get("footnote")
    if fn_raw is None:
        return None
    if not isinstance(fn_raw, str):
        _logger.error(
            "page-row-corrupt",
            urn=book_urn,
            page_number=page,
            footnote_type=type(fn_raw).__name__,
        )
        raise ReaderSourceError(
            f"Corrupt page in {book_urn}: footnote is {type(fn_raw).__name__}, expected str"
        )
    stripped = fn_raw.strip()
    return stripped if stripped else None


def page_rows(book_urn: str) -> list[PageRow]:
    """The single source of a book's (page, content, footnote) rows: load the
    source file and return its validated content rows in source order. Raises
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
        footnote = _row_footnote(book_urn, page, row_dict)
        rows.append(PageRow(page=page, content=body, footnote=footnote))
    return rows


@lru_cache(maxsize=1)
def _toc_override_index() -> dict[str, Any]:
    """Load the synthesized/adapted-TOC override index, or {} when not built.

    The index is a built artifact keyed by URN. An absent file is logged and
    treated as "no overrides" so the reader still serves scraped TOCs; a corrupt
    file surfaces as a JSON load error rather than masquerading as empty.
    """
    path = data_path(ARTIFACT__TOC_INDEX)
    if not path.exists():
        _logger.warning("toc-override-index-absent", path=str(path))
        return {}
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _override_toc(book_urn: str) -> Toc | None:
    """Return a synthesized/adapted TOC for ``book_urn`` when one is indexed.

    These override the scraped source TOC for books whose embedded TOC was empty
    or garbage; each entry is grounded on its real page in our own text.
    """
    record = _toc_override_index().get(book_urn)
    if not isinstance(record, dict):
        return None
    rows = record.get("entries")
    if not isinstance(rows, list):
        return None
    entries: list[TocEntry] = []
    for row in cast(list[Any], rows):
        if not isinstance(row, dict):
            continue
        row_dict = cast(dict[str, Any], row)
        page = row_dict.get("page")
        title = str(row_dict.get("title") or "").strip()
        if isinstance(page, int) and title:
            entries.append(TocEntry(page=page, title=title))
    return Toc(book_urn=book_urn, entries=entries) if entries else None


def try_get_toc(book_urn: str) -> Toc | None:
    """Return the TOC for ``book_urn``, or None when the book has no TOC section.

    A synthesized/adapted TOC in the override index wins over the scraped source
    TOC. Otherwise None is the explicit absent-TOC signal so call sites model
    absence without a try/except. Present-but-corrupt TOC (rows not a list) still
    raises ReaderSourceError — that is corruption, not absence.
    """
    override = _override_toc(book_urn)
    if override is not None:
        return override
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


_NOT_FOUND_STATUS: int = 404


@lru_cache(maxsize=1)
def _backend_client() -> httpx.Client:
    """Return the process-wide sync client bound to the consolidated backend.

    The backend owns the page index; the reader fetches page text, the page
    count, and the footnote block from ``/api/r/page/{urn}/{n}`` here. The base
    URL is the same ``Settings.corpus_search_base_url`` the cross-corpus search
    proxy uses, so one deployment setting points both at the one co-located
    backend. Sync, not async, because this repository is a sync stack serving a
    threadpool route handler with a local sqlite hadith overlay.
    """
    return httpx.Client(
        base_url=get_settings().corpus_search_base_url,
        timeout=HTTP__REQUEST_TIMEOUT_SECONDS,
    )


def _fetch_page(book_urn: str, page_number: int) -> dict[str, Any]:
    """GET one page object from the consolidated backend, mapping status to errors.

    The single network seam for page text. A 404 is the backend's clean
    no-such-page signal and maps to ``ResourceNotFoundError``, a 404 to the
    client. Every other failure, whether a network error, a non-2xx status, a
    non-JSON body, or a non-object body, is a backend contract violation and
    raises ``ReaderSourceError`` so an outage is visible rather than silently
    swallowed. A missing page on the backend is a
    real absence, not a reason to read a stale local copy.
    """
    path = f"/api/r/page/{book_urn}/{page_number}"
    try:
        response = _backend_client().get(path)
    except httpx.HTTPError as exc:
        raise ReaderSourceError(
            f"page backend unreachable for {book_urn}#{page_number}: {exc}"
        ) from exc
    if response.status_code == _NOT_FOUND_STATUS:
        raise ResourceNotFoundError(kind="page", identifier=f"{book_urn}#{page_number}")
    if not response.is_success:
        raise ReaderSourceError(f"page backend {path} returned status {response.status_code}")
    try:
        data = response.json()
    except ValueError as exc:
        raise ReaderSourceError(f"page backend {path} returned non-JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ReaderSourceError(f"page backend {path} returned non-object JSON")
    return cast(dict[str, Any], data)


def get_page(book_urn: str, page_number: int) -> BookPage:
    """Return the requested page or raise ``ResourceNotFoundError``.

    Structured ``hadiths`` (isnad + matn + narrators) come from the manuscript
    index built by Phase 3 extract, via ``manuscript.hadiths_for_page``. When the
    page has parsed hadiths they are served and ``text_ar`` is ``None`` (the two
    are mutually exclusive per the ``BookPage`` contract); otherwise ``text_ar``
    carries the raw page text honestly — for prose pages, or before the index is
    built. ``text_en`` is the single wiring point for an English rendering: the
    corpus has no English column yet, so it stays ``None`` and the reader shows a
    labelled preview; set it here the moment translations land. ``footnotes``
    carries the page's printed apparatus on both shapes: the notes annotate the
    printed page, not the extraction.
    """
    page = _fetch_page(book_urn, page_number)
    total_pages = page.get("total_pages")
    if not isinstance(total_pages, int) or total_pages < 1:
        raise ReaderSourceError(
            f"page backend returned no total_pages for {book_urn}#{page_number}"
        )
    footnote_text = page.get("footnote_text")
    text_ar_raw = page.get("text_ar")
    text_ar = text_ar_raw if isinstance(text_ar_raw, str) else None
    hadiths = manuscript_repo.hadiths_for_page(book_urn, page_number)
    footnotes = (
        [Footnote(marker=marker, text=text) for marker, text in split_footnote_block(footnote_text)]
        if isinstance(footnote_text, str) and footnote_text
        else []
    )
    return BookPage(
        page_number=page_number,
        total_pages=total_pages,
        chapter_title=_chapter_title_at(book_urn, page_number),
        chapter_title_en=None,
        section_title="",
        section_title_en=None,
        hadiths=hadiths,
        text_ar=None if hadiths else text_ar,
        text_en=None,
        footnotes=footnotes,
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
