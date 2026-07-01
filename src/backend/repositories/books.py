"""Repository for book records: backed by ``data/books_index.json``.

The index is produced by ``scripts/ingest_books.py`` and holds:
  * ``books``: every book record as a serialized Book (one row per volume)
  * ``sources``: URN → relative path under ``settings.books_dir`` for the
    underlying source file (used by the reader repository to lazy-load
    TOC + page content)

Loaded once per process at first call via the cached loader. The catalogue
stores one row per physical volume; :func:`list_works` folds those rows by URN
stem into works so the Library lists works, not duplicated volumes.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from backend.core.constants import HTTP__DEFAULT_PAGE_SIZE
from backend.core.errors import ResourceNotFoundError
from backend.core.settings import get_settings
from backend.models.book import Book
from backend.models.work import Work
from backend.patterns import normalize_arabic
from backend.repositories import _taxonomy
from backend.repositories._data_loader import DataLoadError, load_json


@lru_cache(maxsize=1)
def _index() -> tuple[tuple[Book, ...], dict[str, str]]:
    """Return ``(books_in_order, urn_to_relpath)`` from the index file.

    The ``books`` list and ``sources`` map are required: a present-but-wrong
    shape would otherwise serve an empty catalogue as a success. Fail loud
    instead so a corrupt index is fixed, not silently served.
    """
    raw = load_json("books_index.json")
    if not isinstance(raw, dict):
        raise DataLoadError("books_index.json is not a JSON object")
    raw_dict = cast(dict[str, Any], raw)
    books_raw = raw_dict.get("books")
    sources_raw = raw_dict.get("sources")
    if not isinstance(books_raw, list):
        raise DataLoadError("books_index.json is missing a 'books' list")
    if not isinstance(sources_raw, dict):
        raise DataLoadError("books_index.json is missing a 'sources' map")
    books = tuple(Book.model_validate(entry) for entry in cast(list[Any], books_raw))
    return books, dict(cast(dict[str, str], sources_raw))


def list_books(
    category: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[Book], int]:
    """Return ``(slice, total)`` of books, optionally filtered by category."""
    books, _ = _index()
    filtered = [b for b in books if b.category == category] if category is not None else list(books)
    total = len(filtered)
    if limit is None:
        return filtered[offset:], total
    return filtered[offset : offset + limit], total


def _stem(urn: str) -> str:
    """The work key for a volume URN: strip a trailing ``_<digits>`` (the volume
    number). ``VdFfCzwY_01`` -> ``VdFfCzwY``; a suffix-less URN is its own stem."""
    head, sep, tail = urn.rpartition("_")
    return head if sep and head and tail.isdigit() else urn


def _fold_work(stem: str, volumes: list[Book]) -> Work:
    """Fold one stem's volumes into a Work. The volumes must agree on title +
    author: a stem shared by genuinely different works (an original and a
    recension) would otherwise merge into a wrong claim, so a disagreement fails
    loud rather than guessing."""
    ordered = sorted(volumes, key=lambda b: b.volume or 1)
    head = ordered[0]
    for vol in ordered:
        if vol.title_ar != head.title_ar or vol.author_ar != head.author_ar:
            raise DataLoadError(
                f"URN stem '{stem}' folds volumes of differing works: "
                f"'{head.title_ar}' / '{head.author_ar}' vs "
                f"'{vol.title_ar}' / '{vol.author_ar}'"
            )
    pages = [b.page_count for b in ordered if b.page_count is not None]
    return Work(
        stem=stem,
        title_ar=head.title_ar,
        title_en=head.title_en,
        author=head.author,
        author_ar=head.author_ar,
        death_year_ah=head.death_year_ah,
        death_year_ce=head.death_year_ce,
        page_count=sum(pages) if pages else None,
        volume_count=len(ordered),
        category=head.category,
        sect=head.sect,
        canonical=head.canonical,
        volumes=[b.urn for b in ordered],
        first_urn=ordered[0].urn,
    )


@lru_cache(maxsize=1)
def _works() -> tuple[Work, ...]:
    """Every catalogue book folded into works by URN stem, in first-seen order."""
    books, _ = _index()
    groups: dict[str, list[Book]] = {}
    order: list[str] = []
    for book in books:
        stem = _stem(book.urn)
        if stem not in groups:
            groups[stem] = []
            order.append(stem)
        groups[stem].append(book)
    return tuple(_fold_work(stem, groups[stem]) for stem in order)


def _scope_slugs(
    category: str | None, domain: str | None, tradition: str | None
) -> set[str] | None:
    """The set of category slugs a works query targets, or ``None`` for all.
    A category pins one slug; a domain expands to its categories; a tradition
    keeps only that tradition's categories plus the shared/neutral ones."""
    if category:
        return {category}
    if domain is None and not tradition:
        return None
    slugs = set(_taxonomy.DOMAIN_OF) if domain is None else set(_taxonomy.categories_in(domain))
    if tradition in ("sunni", "shia"):
        return {s for s in slugs if _taxonomy.tradition_of(s) in (tradition, "shared")}
    if tradition == "shared":
        return {s for s in slugs if _taxonomy.tradition_of(s) == "shared"}
    return slugs


@dataclass(frozen=True, slots=True)
class WorksQuery:
    """Scope + text filters for a volume-folded works listing."""

    category: str | None = None
    domain: str | None = None
    tradition: str | None = None
    q: str = ""


def list_works(
    query: WorksQuery,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[Work], int]:
    """Return ``(slice, total)`` of volume-folded works, scoped by category,
    domain, and/or tradition, and optionally text-matched on ``q`` (title or
    author, diacritic-insensitive for Arabic and lower-cased for Latin)."""
    scope = _scope_slugs(query.category, query.domain, query.tradition)
    works = list(_works()) if scope is None else [w for w in _works() if w.category in scope]
    needle = query.q.strip()
    if needle:
        fold = normalize_arabic(needle)
        low = needle.lower()
        works = [
            w for w in works if _hit((w.title_ar, w.title_en, w.author, w.author_ar), fold, low)
        ]
    total = len(works)
    if limit is None:
        return works[offset:], total
    return works[offset : offset + limit], total


@lru_cache(maxsize=1)
def category_stats() -> dict[str, tuple[int, int]]:
    """Map each category slug to ``(work_count, volume_count)`` from the live
    index, so the taxonomy's seeded counts can be replaced with real ones."""
    stats: dict[str, tuple[int, int]] = {}
    for work in _works():
        works_n, vols_n = stats.get(work.category, (0, 0))
        stats[work.category] = (works_n + 1, vols_n + work.volume_count)
    return stats


def _field_values(book: Book, field: str) -> tuple[str | None, ...]:
    """The book strings a given search field looks at."""
    if field == "title":
        return (book.title_ar, book.title_en)
    if field == "author":
        return (book.author_ar, book.author)
    return (book.title_ar, book.title_en, book.author_ar, book.author)


def _hit(values: tuple[str | None, ...], fold: str, low: str) -> bool:
    """True if any value contains the query (Arabic fold-insensitive, or latin)."""
    for value in values:
        if not value:
            continue
        if fold and fold in normalize_arabic(value):
            return True
        if low in value.lower():
            return True
    return False


def search_books(
    q: str, field: str = "any", limit: int = HTTP__DEFAULT_PAGE_SIZE, offset: int = 0
) -> tuple[list[Book], int]:
    """Return ``(slice, total)`` of books whose ``field`` (title / author / any)
    matches ``q``, matched diacritic-insensitively for Arabic and lower-cased
    for Latin."""
    needle = q.strip()
    if not needle:
        return [], 0
    fold = normalize_arabic(needle)
    low = needle.lower()
    books, _ = _index()
    matched = [b for b in books if _hit(_field_values(b, field), fold, low)]
    total = len(matched)
    return matched[offset : offset + limit], total


def get_book(urn: str) -> Book:
    """Return the book with the given URN, or raise ResourceNotFoundError."""
    books, _ = _index()
    for book in books:
        if book.urn == urn:
            return book
    raise ResourceNotFoundError(kind="book", identifier=urn)


def source_path(urn: str) -> Path | None:
    """Return the absolute path of the source file for ``urn``, or None."""
    _, sources = _index()
    rel = sources.get(urn)
    if rel is None:
        return None
    return get_settings().books_dir.resolve() / rel
