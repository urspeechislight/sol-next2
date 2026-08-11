"""Tests for the curated TOC overrides validator (backend.build.toc_overrides)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.build import toc_overrides


def _only_known(urn: str) -> Path | None:
    """Resolve only ``known_01`` to a path, so override validation is deterministic."""
    return Path("/x.json") if urn == "known_01" else None


def test_should_shape_valid_overrides_into_records(monkeypatch: pytest.MonkeyPatch) -> None:
    """A known book with real entries becomes a curated {source, entries} record."""
    monkeypatch.setattr(toc_overrides.books_repo, "source_path", _only_known)
    source = {"known_01": {"entries": [{"page": 7, "title": "مقدمة"}]}}
    index = toc_overrides.curated_index(source)
    assert index == {"known_01": {"source": "curated", "entries": [{"page": 7, "title": "مقدمة"}]}}


def test_should_drop_rows_without_a_page_or_title(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rows missing a positive page or a non-empty title are discarded."""
    monkeypatch.setattr(toc_overrides.books_repo, "source_path", _only_known)
    source = {
        "known_01": {
            "entries": [
                {"page": 5, "title": "باب"},
                {"page": 0, "title": "bad"},
                {"page": 9, "title": "  "},
                {"title": "no page"},
            ]
        }
    }
    index = toc_overrides.curated_index(source)
    assert index["known_01"]["entries"] == [{"page": 5, "title": "باب"}]


def test_should_reject_an_unknown_book(monkeypatch: pytest.MonkeyPatch) -> None:
    """A URN with no source book fails the build rather than shipping a silent gap."""
    monkeypatch.setattr(toc_overrides.books_repo, "source_path", _only_known)
    with pytest.raises(SystemExit):
        toc_overrides.curated_index({"ghost_99": {"entries": [{"page": 1, "title": "x"}]}})


def test_should_reject_a_book_with_no_valid_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    """A known book left with no valid entries is a curation error, not an empty TOC."""
    monkeypatch.setattr(toc_overrides.books_repo, "source_path", _only_known)
    with pytest.raises(SystemExit):
        toc_overrides.curated_index({"known_01": {"entries": [{"page": 0, "title": ""}]}})
