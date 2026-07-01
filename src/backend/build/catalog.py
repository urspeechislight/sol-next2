"""Build layer: materialize the book catalog artifact (``data/books_index.json``).

Frontmatter normalizers and the walk/ingest projection that turn the
upstream corpus tree (``settings.books_dir``, ~18.7k JSON files across
category dirs) into the catalog index the backend serves:

    {
      "books": [Book, ...],
      "sources": { "<urn>": "<category>/<file>.json", ... },
      "generated_at": "...iso...",
      "source_root": "...",
      "stats": { "scanned": N, "indexed": N, "skipped": {...} }
    }

This is read-only mirroring of pre-pipeline metadata: title, author, page
count, sect are already structured in the source frontmatter. Isnad,
narrators, translations, and cross-refs arrive through the SQLite artifact
contract (``docs/adr/0001-storage-contract.md``), never here. The CLI shell
lives in ``backend.build.runner``; the numeric pattern compiles through
``backend.patterns.cached_compile`` (CENTRAL-002).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from backend.core.constants import BOOK__DEATH_YEAR_AH_MAX
from backend.core.logging import get_logger
from backend.core.settings import get_settings
from backend.models.book import Book, Canonical
from backend.patterns import cached_compile

_logger = get_logger("shia-library.build")

_CANONICAL_MAP: dict[str, Canonical] = {
    "primary_reference": "primary_reference",
    "primary": "primary",
    "secondary": "secondary",
    "tertiary": "tertiary",
}
_SECT_MAP: dict[str, str] = {
    "sunni": "Sunni",
    "shia": "Imami",
    "imami": "Imami",
    "zaidi": "Zaidi",
    "ismaili": "Ismaili",
}
_MADHAB_MAP: dict[str, str] = {
    "hanafi": "Hanafi",
    "hanbali": "Hanbali",
    "maliki": "Maliki",
    "shafii": "Shafiʿi",
    "shafi": "Shafiʿi",
    "zahiri": "Zahiri",
    "zaidi": "Zaidi",
    "ismaili": "Ismaili",
    "ahl al-bayt": "Imami",
    "jafari": "Imami",
}

_NUMERIC_RE = cached_compile(r"^[+-]?\d+(?:\.\d+)?$")


def _opt_int(value: Any) -> int | None:
    """Coerce a frontmatter value to int. Returns None when not coercible.

    Numeric fields in the frontmatter sometimes arrive as int, sometimes as
    string ('483'), sometimes as float ('30.0' for volume). We accept all
    three and reject anything else without claiming a value; the up-front
    numeric-shape check means no try/except that could swallow a parse
    error or crash the whole ingest on one malformed value. ``bool`` is a
    subclass of ``int`` and is never accepted as a number. ``None`` is the
    explicit "absent / unrecognised shape" return; the caller decides
    whether to skip the record or propagate the absence.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or not _NUMERIC_RE.match(stripped):
        return None
    return int(float(stripped))


def _opt_str(value: Any) -> str | None:
    """Strip + None-ify empty strings; leave non-strings as None."""
    if not isinstance(value, str):
        return None
    s = value.strip()
    return s or None


def _normalize_canonical(raw: Any) -> Canonical | None:
    """Map a raw canonical_status into the schema's Literal values, or None when
    absent/unrecognized. Never invents a rank; an unranked book stays unranked
    rather than being fabricated into ``primary`` (the top editorial rank)."""
    if not isinstance(raw, str):
        return None
    return _CANONICAL_MAP.get(raw.strip().lower())


def _normalize_sect(raw: Any) -> str | None:
    """Map a raw sect/sectarian_affiliation into a tidy display label."""
    if not isinstance(raw, str):
        return None
    return _SECT_MAP.get(raw.strip().lower())


def _normalize_madhab(raw: Any) -> str | None:
    """Map a raw author_sectarian_affiliation into a madhab display label."""
    if not isinstance(raw, str):
        return None
    return _MADHAB_MAP.get(raw.strip().lower())


def _normalize_volume(raw: Any) -> int | None:
    """A volume of 0 in the frontmatter means 'no volume'. Schema requires >= 1."""
    v = _opt_int(raw)
    if v is None or v < 1:
        return None
    return v


def _normalize_death_year(raw: Any) -> int | None:
    """A death year, or None when absent / unrecognised / the upstream sentinel.

    The corpus marks a missing death year with 99999, a value no classical
    author reaches, so it is the "unknown" sentinel, not a date. Coerce it
    (and any implausible value) to None rather than pass a fabricated
    far-future year through to the catalogue. The matching model bound
    (``BOOK__DEATH_YEAR_AH_MAX``) is the defence-in-depth backstop."""
    year = _opt_int(raw)
    if year is None or year < 1 or year > BOOK__DEATH_YEAR_AH_MAX:
        return None
    return year


def _book_from_frontmatter(fm: dict[str, Any], category: str, urn: str) -> Book | None:
    """Build a ``Book`` from a frontmatter dict. Returns None if unusable."""
    title_ar = _opt_str(fm.get("title")) or _opt_str(fm.get("short_title"))
    author_ar = _opt_str(fm.get("author"))
    if not title_ar or not author_ar:
        return None
    return Book(
        urn=urn,
        title_ar=title_ar,
        title_en=_opt_str(fm.get("title_en")) or _opt_str(fm.get("short_title")),
        author=_opt_str(fm.get("author_en")),
        author_ar=author_ar,
        death_year_ah=_normalize_death_year(fm.get("death_year") or fm.get("death_date")),
        death_year_ce=None,
        page_count=_opt_int(fm.get("page_count")),
        volume=_normalize_volume(fm.get("volume")),
        category=category,
        sect=_normalize_sect(fm.get("sectarian_affiliation")),
        madhab=_normalize_madhab(fm.get("author_sectarian_affiliation")),
        canonical=_normalize_canonical(fm.get("canonical_status")),
        language=_opt_str(fm.get("language_en")) or "Arabic",
        blurb=None,
    )


def _urn_for(fm: dict[str, Any], path: Path) -> str:
    """Pick a stable URN. Use ``sol_id`` when present; otherwise the file stem."""
    sol_id = _opt_str(fm.get("sol_id"))
    return sol_id or path.stem


def _ingest_one(path: Path, category: str) -> tuple[Book | None, str | None]:
    """Parse one source file. Returns (book, error_message).

    File I/O and JSON parse errors are NOT caught, by design. If the
    corpus contains an unreadable or malformed file, that's a data
    integrity issue the operator must surface and fix before the ingest
    can proceed. Per-record tolerance would silently skip corruption in a
    body of irreplaceable scholarly text. The shape checks below
    (``not_object`` / ``no_frontmatter`` / ``missing_required_fields``)
    use explicit ``(None, reason)`` returns instead, because they're
    structural classifications rather than failures of the read pipeline.
    """
    with path.open("r", encoding="utf-8") as fh:
        doc: Any = json.load(fh)
    if not isinstance(doc, dict):
        return None, "not_object"
    fm_raw: Any = cast("dict[str, Any]", doc).get("frontmatter")
    if not isinstance(fm_raw, dict):
        return None, "no_frontmatter"
    fm = cast("dict[str, Any]", fm_raw)
    urn = _urn_for(fm, path)
    book = _book_from_frontmatter(fm, category=category, urn=urn)
    if book is None:
        return None, "missing_required_fields"
    return book, None


def _walk(books_dir: Path) -> list[tuple[Path, str]]:
    """Return (file_path, category_slug) for every .json under category dirs."""
    out: list[tuple[Path, str]] = []
    for category_dir in sorted(books_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        for jf in sorted(category_dir.glob("*.json")):
            out.append((jf, category_dir.name))
    return out


def build(out: Path) -> dict[str, object]:
    """Walk the corpus, build the catalog index at ``out``; return report fields."""
    books_dir = get_settings().books_dir.resolve()
    if not books_dir.exists():
        raise SystemExit(f"books dir missing: {books_dir}")

    _logger.info("scan-start", path=str(books_dir))
    work = _walk(books_dir)
    _logger.info("scan-done", files=len(work))

    books: list[Book] = []
    sources: dict[str, str] = {}
    skipped: dict[str, int] = {}
    seen_urns: set[str] = set()
    for file_path, category in work:
        book, err = _ingest_one(file_path, category)
        if err is not None:
            skipped[err] = skipped.get(err, 0) + 1
            _logger.warning("build-book-skipped", path=str(file_path), reason=err)
            continue
        if book is None:
            continue
        if book.urn in seen_urns:
            skipped["duplicate_urn"] = skipped.get("duplicate_urn", 0) + 1
            _logger.warning("build-book-skipped", urn=book.urn, reason="duplicate-urn")
            continue
        seen_urns.add(book.urn)
        books.append(book)
        sources[book.urn] = file_path.relative_to(books_dir).as_posix()

    payload: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_root": str(books_dir),
        "stats": {"scanned": len(work), "indexed": len(books), "skipped": skipped},
        "books": [b.model_dump(mode="json") for b in books],
        "sources": sources,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return {"scanned": len(work), "indexed": len(books), "skipped": sum(skipped.values())}
