"""Pydantic DTOs for cross-corpus full-text search hits + drill-down facets."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CorpusMatch(BaseModel):
    """One full-text hit: the book it occurs in, the page, and an excerpt."""

    model_config = ConfigDict(frozen=True)

    urn: str = Field(description="URN of the matching book (opens in the reader).")
    title_ar: str = Field(description="Arabic title of the book.")
    title_en: str | None = Field(default=None, description="English title, if available.")
    author: str | None = Field(default=None, description="Romanized author of the book, if known.")
    category: str = Field(default="", description="Category slug; resolve via domain taxonomy.")
    volume: int | None = Field(default=None, ge=1, description="Volume number, if known.")
    page: int = Field(ge=1, description="Page the match occurs on.")
    snippet: str = Field(description="Excerpt of the matching page, Arabic.")


class CategoryFacet(BaseModel):
    """How many matches a category holds, for the category filter."""

    model_config = ConfigDict(frozen=True)

    slug: str = Field(description="Category slug (resolve label via the domain taxonomy).")
    count: int = Field(ge=0, description="Matching pages in this category.")


class BookFacet(BaseModel):
    """How many matches a book (work, by title) holds, for the book filter."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(description="Arabic book title (groups a work's volumes); the filter key.")
    title_en: str | None = Field(default=None, description="English book title, for display.")
    count: int = Field(ge=0, description="Matching pages in this book across its volumes.")


class VolumeFacet(BaseModel):
    """How many matches a volume number holds, for the volume filter."""

    model_config = ConfigDict(frozen=True)

    volume: int = Field(ge=1, description="Volume number present in the results.")
    count: int = Field(ge=0, description="Matching pages in this volume.")


class SearchFacets(BaseModel):
    """Drill-down filters for the current query: categories, then books within
    the chosen category, then volumes within the chosen book."""

    model_config = ConfigDict(frozen=True)

    categories: list[CategoryFacet] = Field(description="Categories with matches, by count desc.")
    books: list[BookFacet] = Field(description="Books in the chosen category, by count desc.")
    volumes: list[VolumeFacet] = Field(description="Volumes in the chosen book, ascending.")
