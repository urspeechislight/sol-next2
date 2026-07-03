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
from typing import Any, Literal, cast

from backend.core.constants import ARTIFACT__BOOKS_INDEX
from backend.core.errors import ResourceNotFoundError
from backend.core.settings import get_settings
from backend.models.book import CANONICAL_TIERS, Book, Canonical
from backend.models.work import Work
from backend.patterns import normalize_arabic
from backend.repositories import _taxonomy
from backend.repositories._data_loader import DataLoadError, load_json, slice_page


@lru_cache(maxsize=1)
def _index() -> tuple[tuple[Book, ...], dict[str, str]]:
    """Return ``(books_in_order, urn_to_relpath)`` from the index file.

    The ``books`` list and ``sources`` map are required: a present-but-wrong
    shape would otherwise serve an empty catalogue as a success. Fail loud
    instead so a corrupt index is fixed, not silently served.
    """
    raw = load_json(ARTIFACT__BOOKS_INDEX)
    if not isinstance(raw, dict):
        raise DataLoadError(f"{ARTIFACT__BOOKS_INDEX} is not a JSON object")
    raw_dict = cast(dict[str, Any], raw)
    books_raw = raw_dict.get("books")
    sources_raw = raw_dict.get("sources")
    if not isinstance(books_raw, list):
        raise DataLoadError(f"{ARTIFACT__BOOKS_INDEX} is missing a 'books' list")
    if not isinstance(sources_raw, dict):
        raise DataLoadError(f"{ARTIFACT__BOOKS_INDEX} is missing a 'sources' map")
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
    return slice_page(filtered, limit, offset)


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


WorkSort = Literal["canonical", "death_year_ah", "title_ar", "volume_count"]

_UNRANKED_TIER = len(CANONICAL_TIERS)


def _canonical_tier(work: Work) -> int:
    """The work's served editorial-rank tier, with unranked works after every
    ranked tier so the sort key is total."""
    return _UNRANKED_TIER if work.canonical_tier is None else work.canonical_tier


@dataclass(frozen=True, slots=True)
class WorksQuery:
    """Scope + text filters + ordering for a volume-folded works listing.

    ``sort`` draws from the closed ``WorkSort`` set; it is a Literal so the
    API layer rejects an unknown ``?sort=`` with a 422 instead of silently
    serving storage order.
    """

    category: str | None = None
    domain: str | None = None
    tradition: str | None = None
    canonical: Canonical | None = None
    q: str = ""
    sort: WorkSort | None = None


def _order_works(works: list[Work], sort: WorkSort | None) -> list[Work]:
    """Deterministic ordering for a browse dimension; storage order when None.

    ``canonical`` leads with the most authoritative editorial tier, ordering
    within each tier by death year ascending (undated last) then title, so a
    small slice reads as "the works that anchor this scope". ``death_year_ah``
    sorts the dated works ascending with the undated block last (35% of the
    corpus is undated; it is a first-class shelf, not an interleaved gap).
    ``title_ar`` collates on the diacritic-folded Arabic title.
    ``volume_count`` sorts deepest works first, pages as tiebreak.
    """
    if sort is None:
        return works
    if sort == "canonical":
        return sorted(
            works,
            key=lambda w: (
                _canonical_tier(w),
                w.death_year_ah is None,
                w.death_year_ah or 0,
                normalize_arabic(w.title_ar),
            ),
        )
    if sort == "death_year_ah":
        return sorted(
            works,
            key=lambda w: (
                w.death_year_ah is None,
                w.death_year_ah or 0,
                normalize_arabic(w.title_ar),
            ),
        )
    if sort == "title_ar":
        return sorted(works, key=lambda w: normalize_arabic(w.title_ar))
    return sorted(
        works,
        key=lambda w: (-w.volume_count, -(w.page_count or 0), normalize_arabic(w.title_ar)),
    )


def list_works(
    query: WorksQuery,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[Work], int]:
    """Return ``(slice, total)`` of volume-folded works, scoped by category,
    domain, and/or tradition, optionally narrowed to one canonical rank (the
    Library's landmark rotations ask for ``primary_reference``), and optionally
    text-matched on ``q`` (title or author, diacritic-insensitive for Arabic
    and lower-cased for Latin)."""
    scope = _scope_slugs(query.category, query.domain, query.tradition)
    works = list(_works()) if scope is None else [w for w in _works() if w.category in scope]
    if query.canonical is not None:
        works = [w for w in works if w.canonical == query.canonical]
    needle = query.q.strip()
    if needle:
        fold = normalize_arabic(needle)
        low = needle.lower()
        works = [
            w for w in works if _hit((w.title_ar, w.title_en, w.author, w.author_ar), fold, low)
        ]
    return slice_page(_order_works(works, query.sort), limit, offset)


@lru_cache(maxsize=1)
def category_stats() -> dict[str, tuple[int, int]]:
    """Map each category slug to ``(work_count, volume_count)`` from the live
    index, so the taxonomy's seeded counts can be replaced with real ones."""
    stats: dict[str, tuple[int, int]] = {}
    for work in _works():
        works_n, vols_n = stats.get(work.category, (0, 0))
        stats[work.category] = (works_n + 1, vols_n + work.volume_count)
    return stats


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


def get_book(urn: str) -> Book:
    """Return the book with the given URN, or raise ResourceNotFoundError."""
    books, _ = _index()
    for book in books:
        if book.urn == urn:
            return book
    raise ResourceNotFoundError(kind="book", identifier=urn)


def list_volumes(urn: str) -> list[Book]:
    """Return every volume of the work containing ``urn``, ascending by volume
    number: the reader's volume switcher. A single-volume work returns just
    that book. The membership comes from the same fold :func:`list_works`
    serves, so the two views can never disagree; a fold entry missing from the
    index would be an invariant breach and raises KeyError loudly."""
    book = get_book(urn)
    stem = _stem(book.urn)
    work = next((w for w in _works() if w.stem == stem), None)
    if work is None:
        raise ResourceNotFoundError(kind="work", identifier=stem)
    books, _ = _index()
    by_urn = {b.urn: b for b in books}
    return [by_urn[member] for member in work.volumes]


def source_path(urn: str) -> Path | None:
    """Return the absolute path of the source file for ``urn``, or None."""
    _, sources = _index()
    rel = sources.get(urn)
    if rel is None:
        return None
    return get_settings().books_dir.resolve() / rel
