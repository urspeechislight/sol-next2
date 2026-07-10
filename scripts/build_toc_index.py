#!/usr/bin/env python3
"""Build the synthesized-TOC override index for books with an empty/garbage TOC.

Iterates the sourced-book corpus; for each book whose scraped table of contents
is empty or down to a couple of unusable rows, tries to synthesize a real TOC
from the page body (``backend.build.toc_synth``). Books that yield a
letter-section or numbered-entry structure are written to
``data/toc_index.json`` keyed by URN; the reader serves that override ahead of
the scraped TOC (``repositories.reader.try_get_toc``). Books with no clean
structure are left out; the reader keeps serving their scraped TOC or absence.

Curated per-book overrides in ``data/toc_overrides.json`` (``backend.build.toc_overrides``)
are merged last and win over synthesis, for books whose real TOC the body does not
spell out in a detectable form.

Run on titan::

    uv run python scripts/build_toc_index.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from backend.build import toc_overrides, toc_synth
from backend.core.constants import (
    ARTIFACT__BOOKS_INDEX,
    ARTIFACT__TOC_INDEX,
    ARTIFACT__TOC_OVERRIDES,
    TOC_SYNTH__MIN_CONTENT_PAGES,
    TOC_SYNTH__SCRAPED_SPARSE_MAX,
)
from backend.core.logging import configure_logging, get_logger
from backend.core.paths import data_path
from backend.core.settings import get_settings

_logger = get_logger("shia-library.build")


def _section_rows(section: object) -> list[Any]:
    """Return the row list from a single-book-keyed toc/content section."""
    if isinstance(section, dict) and section:
        first = next(iter(section))
        rows = section[first]
        return rows if isinstance(rows, list) else []
    return section if isinstance(section, list) else []


def _scraped_size(doc: dict[str, Any]) -> int:
    """Count usable rows in the scraped TOC section."""
    return sum(
        1
        for row in _section_rows(doc.get("toc"))
        if isinstance(row, dict) and (row.get("title") or "").strip()
    )


def _load_doc(path: Path) -> dict[str, Any]:
    """Load one source-book JSON object, raising loudly on a missing/corrupt file."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise TypeError(f"source-book at {path} is not a JSON object")
    return cast(dict[str, Any], doc)


def _curated_index() -> dict[str, dict[str, Any]]:
    """Load and validate the curated per-book TOC overrides, or {} when absent."""
    path = data_path(ARTIFACT__TOC_OVERRIDES)
    if not path.exists():
        return {}
    source = json.loads(path.read_text(encoding="utf-8"))
    return toc_overrides.curated_index(source)


def _build(out: Path) -> dict[str, int]:
    """Synthesize TOCs for empty/garbage-TOC books and write the override index."""
    books_dir = get_settings().books_dir.resolve()
    sources = json.loads(data_path(ARTIFACT__BOOKS_INDEX).read_text(encoding="utf-8"))["sources"]
    index: dict[str, dict[str, Any]] = {}
    counts: dict[str, int] = {"letters": 0, "numbered": 0, "absent": 0}
    for urn, rel in sources.items():
        path = books_dir / rel
        if not path.exists():
            _logger.warning("toc-index-source-absent", urn=urn, path=str(path))
            counts["absent"] += 1
            continue
        doc = _load_doc(path)
        content_rows = _section_rows(doc.get("content"))
        if len(content_rows) < TOC_SYNTH__MIN_CONTENT_PAGES:
            continue
        if _scraped_size(doc) > TOC_SYNTH__SCRAPED_SPARSE_MAX:
            continue
        result = toc_synth.synthesize(content_rows)
        if result["method"] == "none":
            continue
        index[urn] = {"source": result["method"], "entries": result["entries"]}
        counts[result["method"]] += 1
    curated = _curated_index()
    index.update(curated)
    counts["curated"] = len(curated)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"books": len(index), **counts}


def main() -> None:
    """Run the TOC override-index build CLI."""
    configure_logging()
    parser = argparse.ArgumentParser(description="Build the synthesized-TOC override index.")
    parser.add_argument("--out", type=Path, default=data_path(ARTIFACT__TOC_INDEX))
    args = parser.parse_args()
    report = _build(args.out)
    _logger.info("build-complete", out=str(args.out), **report)


if __name__ == "__main__":
    main()
