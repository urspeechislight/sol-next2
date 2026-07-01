#!/usr/bin/env python3
"""Build the manuscript index (``data/manuscript.db``): span + entity + unit.

Segments then extracts every catalog book (Phase 1 page rows -> segment ->
extract) and writes one row per span, entity, and unit into the read-only
manuscript store. The book's TOC anchors the hierarchy split; the book's category
feeds segment's genre gating. A book whose source is missing, or that segments to
no spans, is skipped (logged). All SQL lives in ``backend.build.manuscript``; this
script only drives segment+extract and projects rows. Pilot a subset with
``--limit N``::

    uv run python scripts/build_manuscript_index.py --limit 5
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from backend.build import manuscript as manuscript_build
from backend.core.constants import CORPUS__BUILD_COMMIT_EVERY
from backend.core.logging import configure_logging, get_logger
from backend.core.paths import data_path
from backend.models.book import Book
from backend.pipeline.config import Config, load_config
from backend.pipeline.extract import extract
from backend.pipeline.models import Manuscript, ManuscriptPage
from backend.pipeline.segment import segment
from backend.repositories import books as books_repo
from backend.repositories import reader as reader_repo

_logger = get_logger("shia-library.manuscript-build")
_DEFAULT_OUT = data_path("manuscript.db")


def _toc_entries(book_urn: str) -> list[dict[str, Any]]:
    """Project a book's TOC into segment's {page_number, title} anchor list.

    Returns [] when the book has no TOC (try_get_toc is None) — segment then
    relies entirely on pattern-based boundaries, which is legitimate.
    """
    toc = reader_repo.try_get_toc(book_urn)
    if toc is None:
        return []
    return [{"page_number": entry.page, "title": entry.title} for entry in toc.entries]


def _process_book(book: Book, config: Config) -> Manuscript | None:
    """Segment then extract one book's pages; return the manuscript, or None if page-less.

    Lets ReaderSourceError (a corrupt page row) propagate so the build fails
    loudly rather than writing a silently-incomplete index.
    """
    rows = reader_repo.page_rows(book.urn)
    if not rows:
        return None
    pages = [
        ManuscriptPage(page_number=row.page, page_name=str(row.page), text=row.content)
        for row in rows
    ]
    manuscript = Manuscript(
        work_id=book.urn,
        manifestation_id=book.urn,
        pages=pages,
        metadata={"book_type": book.category, "toc": _toc_entries(book.urn)},
    )
    return extract(segment(manuscript, config), config)


def build(out: Path, limit: int | None = None) -> tuple[int, int, int, int]:
    """Materialize the manuscript store at ``out``.

    Returns (n_books, n_spans, n_entities, n_units).
    """
    config = load_config()
    out.parent.mkdir(parents=True, exist_ok=True)
    con = manuscript_build.create_span_store(out)
    books, _ = books_repo.list_books()
    if limit is not None:
        books = books[:limit]
    n_books = n_spans = n_entities = n_units = 0
    n_skipped = 0
    try:
        for book in books:
            source = books_repo.source_path(book.urn)
            if source is None or not source.exists():
                _logger.warning("manuscript-book-skipped", urn=book.urn, reason="source-missing")
                n_skipped += 1
                continue
            manuscript = _process_book(book, config)
            if manuscript is None or not manuscript.spans:
                n_skipped += 1
                continue
            manuscript_build.insert_spans(con, manuscript_build.span_rows(manuscript))
            manuscript_build.insert_entities(con, manuscript_build.entity_rows(manuscript))
            manuscript_build.insert_units(con, manuscript_build.unit_rows(manuscript))
            n_books += 1
            n_spans += len(manuscript.spans)
            n_entities += len(manuscript.entities)
            n_units += len(manuscript.units)
            if n_books % CORPUS__BUILD_COMMIT_EVERY == 0:
                con.commit()
        con.commit()
    finally:
        con.close()
    if n_skipped:
        _logger.info("manuscript-build-skipped", count=n_skipped)
    return n_books, n_spans, n_entities, n_units


def main() -> None:
    """Parse args, build the manuscript index, log counts + elapsed."""
    configure_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, default=None, help="process only the first N books (pilot)"
    )
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = parser.parse_args()
    start = time.monotonic()
    n_books, n_spans, n_entities, n_units = build(args.out, limit=args.limit)
    elapsed = time.monotonic() - start
    _logger.info(
        "manuscript-built",
        path=str(args.out),
        elapsed_s=round(elapsed),
        book_count=n_books,
        span_count=n_spans,
        entity_count=n_entities,
        unit_count=n_units,
    )


if __name__ == "__main__":
    main()
