"""Pydantic DTOs for cross-corpus full-text search hits + drill-down facets.

``SearchMode`` is the closed match-mode vocabulary. It lives here, with the
search DTOs, so the API layer (which validates ``?mode=``) and the corpus
repository (which turns a mode into match windows) consume one definition.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from backend.models._base import FrozenModel

SearchMode = Literal["exact", "broad"]


class CorpusMatch(FrozenModel):
    """One full-text hit: the book it occurs in, the page, and an excerpt."""

    urn: str = Field(description="URN of the matching book (opens in the reader).")
    title_ar: str = Field(description="Arabic title of the book.")
    title_en: str | None = Field(default=None, description="English title, if available.")
    author: str | None = Field(default=None, description="Romanized author of the book, if known.")
    category: str = Field(default="", description="Category slug; resolve via domain taxonomy.")
    volume: int | None = Field(default=None, ge=1, description="Volume number, if known.")
    page: int = Field(ge=1, description="Page the match occurs on.")
    snippet: str = Field(description="Excerpt of the matching page, Arabic.")


class CategoryFacet(FrozenModel):
    """How many matches a category holds, for the category filter."""

    slug: str = Field(description="Category slug (resolve label via the domain taxonomy).")
    count: int = Field(ge=0, description="Matching pages in this category.")


class BookFacet(FrozenModel):
    """How many matches a book (work, by title) holds, for the book filter."""

    title: str = Field(description="Arabic book title (groups a work's volumes); the filter key.")
    title_en: str | None = Field(default=None, description="English book title, for display.")
    count: int = Field(ge=0, description="Matching pages in this book across its volumes.")


class VolumeFacet(FrozenModel):
    """How many matches a volume number holds, for the volume filter."""

    volume: int = Field(ge=1, description="Volume number present in the results.")
    count: int = Field(ge=0, description="Matching pages in this volume.")


class SearchFacets(FrozenModel):
    """Drill-down filters for the current query: categories, then books within
    the chosen category, then volumes within the chosen book."""

    categories: list[CategoryFacet] = Field(description="Categories with matches, by count desc.")
    books: list[BookFacet] = Field(description="Books in the chosen category, by count desc.")
    volumes: list[VolumeFacet] = Field(description="Volumes in the chosen book, ascending.")
