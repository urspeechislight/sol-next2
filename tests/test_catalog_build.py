"""Tests for the catalog ingest projection in ``backend.build.catalog``."""

from __future__ import annotations

from backend.build.catalog import _book_from_frontmatter


def test_should_build_book_when_frontmatter_has_title_and_author() -> None:
    """A fully-authored volume builds with both author fields populated."""
    book = _book_from_frontmatter(
        {"title": "كتاب", "author": "المؤلف", "author_en": "Author"},
        category="sunni-theology",
        urn="Xyz12345",
    )
    assert book is not None
    assert book.author_ar == "المؤلف"
    assert book.author == "Author"


def test_should_build_authorless_book_when_text_is_anonymous() -> None:
    """Scripture and other anonymous corporate texts index with author None."""
    book = _book_from_frontmatter(
        {"title": "עמוס", "title_en": "Amos"},
        category="bible-tanakh",
        urn="bib-tanakh-amos_1",
    )
    assert book is not None
    assert book.title_ar == "עמוס"
    assert book.author_ar is None
    assert book.author is None


def test_should_reject_frontmatter_without_a_title() -> None:
    """A titleless record is unusable and is skipped as missing required fields."""
    assert _book_from_frontmatter({"author": "المؤلف"}, category="c", urn="u") is None
