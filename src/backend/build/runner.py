"""Build layer: the machinery every artifact build shares.

Each read-only artifact (corpus.db, manuscript.db, registry.db,
books_index.json) used to repeat the same shell: wipe-and-recreate the
output, iterate the catalog, skip-and-log books whose source is missing,
bulk-insert with periodic commits, and report counts + elapsed time through
its own argparse/logging arrangement. This module owns that shell once:

  ``create_artifact``        wipe + mkdir + connect + apply schema
  ``finalize``               ANALYZE + VACUUM for artifacts that want it
  ``build_catalog_artifact`` the catalog iteration loop
  ``run_build_cli``          the argparse/logging/timing shell

The per-artifact modules (``corpus``, ``manuscript``, ``rijal``,
``catalog``) own only their schema, their INSERT statements (as a
``tables`` mapping of table name to INSERT SQL), and their row projections.
CENTRAL-005 permits the artifact SQL in this package.
"""

from __future__ import annotations

import argparse
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from backend.core.constants import BUILD__COMMIT_EVERY
from backend.core.logging import configure_logging, get_logger
from backend.models.book import Book
from backend.repositories import books as books_repo

_logger = get_logger("shia-library.build")

ProjectFn = Callable[[Book], dict[str, list[dict[str, Any]]] | None]
FinishFn = Callable[[sqlite3.Connection, list[Book]], dict[str, int]]
BuildFn = Callable[[argparse.Namespace], dict[str, object]]
AddArgsFn = Callable[[argparse.ArgumentParser], None]


def create_artifact(out: Path, schema: str) -> sqlite3.Connection:
    """Wipe any artifact at ``out`` and return a fresh connection with ``schema`` applied."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    con = sqlite3.connect(out)
    con.executescript(schema)
    return con


def finalize(con: sqlite3.Connection) -> None:
    """Optimize a freshly built artifact (statistics + compaction).

    Deliberately opt-in per artifact: VACUUM doubles peak disk, which is
    fine for the megabyte-scale stores and prohibitive for the 40 GB
    corpus index.
    """
    con.execute("ANALYZE")
    con.execute("VACUUM")


def build_catalog_artifact(
    out: Path,
    schema: str,
    tables: dict[str, str],
    project: ProjectFn,
    *,
    limit: int | None = None,
    optimize: bool = False,
    finish: FinishFn | None = None,
) -> dict[str, object]:
    """Materialize one catalog-driven artifact at ``out``; return report fields.

    Iterates the catalog, skipping (with one uniform log shape) books whose
    source file is missing or whose ``project`` callback returns ``None``.
    ``project`` maps one book to ``{table_name: rows}``; every table name
    must exist in ``tables`` (its INSERT statement). Commits every
    ``BUILD__COMMIT_EVERY`` books. ``finish`` runs after the loop on the
    still-open connection for epilogue tables built from the whole catalog.
    A corrupt source raises out of ``project`` and aborts the build loudly;
    a partially written artifact must never pass for a complete one.
    """
    con = create_artifact(out, schema)
    books, _ = books_repo.list_books()
    if limit is not None:
        books = books[:limit]
    counts: dict[str, int] = dict.fromkeys(tables, 0)
    n_books = n_skipped = 0
    try:
        for book in books:
            source = books_repo.source_path(book.urn)
            if source is None or not source.exists():
                _logger.warning("build-book-skipped", urn=book.urn, reason="source-missing")
                n_skipped += 1
                continue
            projected = project(book)
            if projected is None:
                _logger.warning("build-book-skipped", urn=book.urn, reason="no-rows")
                n_skipped += 1
                continue
            for table, rows in projected.items():
                con.executemany(tables[table], rows)
                counts[table] += len(rows)
            n_books += 1
            if n_books % BUILD__COMMIT_EVERY == 0:
                con.commit()
                _logger.info("build-progress", books=n_books, **counts)
        con.commit()
        finish_counts = finish(con, books) if finish is not None else {}
        con.commit()
        if optimize:
            finalize(con)
    finally:
        con.close()
    report: dict[str, object] = {"books": n_books, "skipped": n_skipped}
    report.update(counts)
    report.update(finish_counts)
    return report


def run_build_cli(
    description: str,
    default_out: Path,
    build_fn: BuildFn,
    *,
    supports_limit: bool = True,
    add_args: AddArgsFn | None = None,
) -> None:
    """Run one artifact build as a CLI: parse args, time it, log one report.

    Every build gets ``--out``, configured logging, and an identical
    ``build-complete`` report under the one build logger, so no artifact
    script re-invents its own shell. ``--limit`` is offered only when the
    build is catalog-driven; a flag that silently does nothing is worse
    than no flag.
    """
    configure_logging()
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--out", type=Path, default=default_out)
    if supports_limit:
        parser.add_argument(
            "--limit", type=int, default=None, help="process only the first N books (pilot)"
        )
    if add_args is not None:
        add_args(parser)
    args = parser.parse_args()
    start = time.monotonic()
    report = build_fn(args)
    _logger.info(
        "build-complete",
        out=str(args.out),
        elapsed_s=round(time.monotonic() - start),
        **report,
    )
