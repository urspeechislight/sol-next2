"""The exclusion manifest stays enforced: no excluded URN is ever served."""

from __future__ import annotations

import json

from backend.core.paths import config_path
from backend.repositories import books as books_repo


def _manifest_urns() -> set[str]:
    """The excluded URNs as checked in under ``config/``."""
    with config_path("catalog_exclusions.json").open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    urns = set(manifest["urns"])
    assert urns, "exclusion manifest must not be empty"
    return urns


def test_should_keep_every_excluded_urn_out_of_the_catalog() -> None:
    """A rebuilt index must not resurrect editorially removed volumes.

    Regression for the 2026-06-30 rebuild that re-served the 588 volumes of
    the Persian-equivalent purge because the ingest had no exclusion step.
    """
    excluded = _manifest_urns()
    served, _total = books_repo.list_books()
    resurrected = {b.urn for b in served} & excluded
    assert not resurrected, f"excluded urns served by the catalog: {sorted(resurrected)[:5]}"
