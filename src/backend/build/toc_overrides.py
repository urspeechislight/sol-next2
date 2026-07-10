"""Validate curated, hand-authored TOC overrides for the reader's override index.

The automated ``toc_synth`` detectors only recover structure a book states in its
own body (``حرف X`` sections, ``N -`` numbered entries). Some books need a TOC that
the body does not spell out that way: here Siyar A'lam al-Nubala vol.1, whose intro
chapters carry no numeric marker and whose scraped TOC was four unusable rows. For
those, an entry is authored once against a trusted edition and stored in the tracked
``data/toc_overrides.json``. ``scripts/build_toc_index.py`` merges the result over
the synthesized index (curated wins), so both feed the one artifact the reader loads.
"""

from __future__ import annotations

from typing import Any

from backend.repositories import books as books_repo


def _clean_entries(urn: str, rows: Any) -> list[dict[str, Any]]:
    """Return one book's override rows that carry a positive page and a title."""
    if not isinstance(rows, list):
        raise SystemExit(f"toc override for {urn}: 'entries' is not a list")
    clean: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        page = row.get("page")
        title = str(row.get("title") or "").strip()
        if isinstance(page, int) and page >= 1 and title:
            clean.append({"page": page, "title": title})
    return clean


def curated_index(source: dict[str, Any]) -> dict[str, Any]:
    """Validate the curated overrides and shape them into override-index records.

    A URN with no source book, a non-object record, or no valid entries is a
    curation error and fails the build loudly rather than shipping a silent gap.
    """
    index: dict[str, Any] = {}
    for urn, record in source.items():
        if books_repo.source_path(urn) is None:
            raise SystemExit(f"toc override for unknown book urn: {urn}")
        if not isinstance(record, dict):
            raise SystemExit(f"toc override for {urn} is not an object")
        entries = _clean_entries(urn, record.get("entries"))
        if not entries:
            raise SystemExit(f"toc override for {urn} has no valid entries")
        index[urn] = {"source": "curated", "entries": entries}
    return index
