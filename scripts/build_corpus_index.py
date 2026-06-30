#!/usr/bin/env python3
"""Build the corpus full-text index (``data/corpus.db``).

Scans every catalog book's source file (via the one public page accessor,
``reader.page_rows``) and inserts each page TWICE: a ``fold`` column (text put
through ``patterns.fold_search`` — diacritics + annotation signs stripped,
alef/yaa/taa folded) which FTS5 indexes for matching, and the original
``content`` (UNINDEXED) for fold-aware snippet display. Then writes a small
``book(urn, category, title, volume)`` table for the search filters. The
artifact is large (it stores both forms); no ``optimize`` pass. All SQL lives in
``backend.repositories.corpus``; this script only projects rows. Run on buildhost::

    uv run python scripts/build_corpus_index.py
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Final

from backend.core.constants import CORPUS__BUILD_COMMIT_EVERY
from backend.core.logging import get_logger
from backend.core.paths import data_path
from backend.patterns import fold_search
from backend.repositories import books as books_repo
from backend.repositories import corpus as corpus_repo
from backend.repositories import reader as reader_repo

_logger = get_logger("shia-library.corpus-build")
_DEFAULT_OUT = data_path("corpus.db")
_BYTES_PER_GIB: Final[int] = 1024**3


def _index_rows(urn: str) -> list[dict[str, Any]]:
    """Project one book's page rows into corpus index rows (folded + original)."""
    return [
        {"fold": fold_search(r.content), "content": r.content, "urn": urn, "page": r.page}
        for r in reader_repo.page_rows(urn)
    ]


def build(out: Path) -> tuple[int, int]:
    """Materialize the FTS index + book table at ``out``; return ``(n_books, n_pages)``."""
    out.parent.mkdir(parents=True, exist_ok=True)
    con = corpus_repo.create_index(out)
    books, _ = books_repo.list_books()
    n_books = n_pages = 0
    n_missing = n_empty = 0
    try:
        for book in books:
            path = books_repo.source_path(book.urn)
            if path is None or not path.exists():
                _logger.warning("index-book-skipped", urn=book.urn, reason="source-missing")
                n_missing += 1
                continue
            # A corrupt page row raises ReaderSourceError here; let it propagate so
            # the build crashes loudly rather than writing a silently-incomplete index.
            rows = _index_rows(book.urn)
            if not rows:
                _logger.warning("index-book-skipped", urn=book.urn, reason="no-rows")
                n_empty += 1
                continue
            corpus_repo.insert_pages(con, rows)
            n_books += 1
            n_pages += len(rows)
            if n_books % CORPUS__BUILD_COMMIT_EVERY == 0:
                con.commit()
                print(f"...{n_books} books, {n_pages} pages indexed", flush=True)
        con.commit()
        corpus_repo.build_book_table(con, corpus_repo.book_table_rows(books))
        con.commit()
    finally:
        con.close()
    skipped = n_missing + n_empty
    if skipped:
        print(
            f"skipped {skipped} books: {n_missing} source-missing, {n_empty} no-rows",
            flush=True,
        )
    return n_books, n_pages


def main() -> None:
    """Build the corpus index and report counts + size."""
    t0 = time.monotonic()
    n_books, n_pages = build(_DEFAULT_OUT)
    elapsed = time.monotonic() - t0
    size_gib = _DEFAULT_OUT.stat().st_size / _BYTES_PER_GIB
    print(
        f"Built {_DEFAULT_OUT} in {elapsed:.0f}s: {n_books} books, "
        f"{n_pages} pages, {size_gib:.1f} GiB"
    )


if __name__ == "__main__":
    main()
