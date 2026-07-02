#!/usr/bin/env python3
"""Build the manuscript index (``data/manuscript.db``): span + entity + unit.

Segments then extracts every catalog book (Phase 1 page rows -> segment ->
extract) and writes one row per span, entity, and unit into the read-only
manuscript store. The book's TOC anchors the hierarchy split; the book's
category feeds segment's genre gating. Thin driver: row projections and SQL
live in ``backend.build.manuscript``; the build loop and CLI shell live in
``backend.build.runner``. Pilot a subset with ``--limit N``::

    uv run python scripts/build_manuscript_index.py --limit 5
"""

from __future__ import annotations

import argparse
from typing import Any

from backend.build import manuscript as manuscript_build
from backend.build import runner
from backend.build.narrator_link import NarratorLinker, annotate_manuscript
from backend.core.paths import data_path
from backend.models.book import Book
from backend.pipeline.config import Config, load_config
from backend.pipeline.extract import extract
from backend.pipeline.models import Manuscript, ManuscriptPage
from backend.pipeline.segment import segment
from backend.repositories import reader as reader_repo


def _toc_entries(book_urn: str) -> list[dict[str, Any]]:
    """Project a book's TOC into segment's {page_number, title} anchor list.

    Returns [] when the book has no TOC (try_get_toc is None); segment then
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


def _build(args: argparse.Namespace) -> dict[str, object]:
    """Run segment+extract over the catalog and materialize the span store.

    Narrator entities are linked to the registry at build time (the join the
    reader used to approximate in the browser against a 600-row sample); the
    link rides in entity metadata, so the artifact schema is unchanged.
    """
    config = load_config()
    linker = NarratorLinker.from_registry()

    def _project(book: Book) -> dict[str, list[dict[str, Any]]] | None:
        manuscript = _process_book(book, config)
        if manuscript is None or not manuscript.spans:
            return None
        annotate_manuscript(manuscript, linker)
        return {
            "span": manuscript_build.span_rows(manuscript),
            "entity": manuscript_build.entity_rows(manuscript),
            "unit": manuscript_build.unit_rows(manuscript),
        }

    return runner.build_catalog_artifact(
        args.out,
        manuscript_build.MANUSCRIPT_SCHEMA,
        manuscript_build.TABLES,
        _project,
        limit=args.limit,
    )


def main() -> None:
    """Run the manuscript index build CLI."""
    runner.run_build_cli(
        "Build the manuscript span/entity/unit store via segment+extract.",
        data_path("manuscript.db"),
        _build,
    )


if __name__ == "__main__":
    main()
