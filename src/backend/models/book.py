"""Pydantic DTOs for book + work records.

A physical book volume and a volume-folded work share one block of bibliographic
fields (title, author, death years, pages, category, sect, rank). That block is
defined once on :class:`BibRecord`; :class:`Book` and
:class:`~backend.models.work.Work` each extend it with their own identity fields,
so the shared shape never drifts between the two.

``Book`` itself has two populating sources:

  1. The curated 8-book sample (rich English + blurb, hand-edited).
  2. The real corpus ingest from frontmatter, which has no editorial blurb
     and uses ``primary_reference`` for canonical status. The schema is
     permissive on those fields so both shapes round-trip without lossy
     coercion.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.core.constants import BOOK__DEATH_YEAR_AH_MAX

Canonical = Literal["primary", "primary_reference", "secondary", "tertiary"]


class BibRecord(BaseModel):
    """Bibliographic fields shared by a book volume and a folded work."""

    model_config = ConfigDict(frozen=True)

    title_ar: str = Field(description="Arabic title.")
    title_en: str | None = Field(default=None, description="English title, if available.")
    author: str | None = Field(default=None, description="Author in romanized form.")
    author_ar: str = Field(description="Author in Arabic.")
    death_year_ah: int | None = Field(
        default=None,
        ge=1,
        le=BOOK__DEATH_YEAR_AH_MAX,
        description="Author's death year, Hijri (unknown is None, never a sentinel).",
    )
    death_year_ce: int | None = Field(default=None, description="Author's death year, CE.")
    page_count: int | None = Field(default=None, ge=0, description="Page count, if known.")
    category: str = Field(description="Category slug (matches Domain.categories[].slug).")
    sect: str | None = Field(default=None, description="Sect tagging (Imami, Sunni, etc.).")
    canonical: Canonical | None = Field(default=None, description="Editorial rank, or None.")


class Book(BibRecord):
    """One book record (a single physical volume) exposed by the screens."""

    urn: str = Field(description="Opaque URN identifying the book across screens.")
    volume: int | None = Field(default=None, ge=1, description="Volume number, if multi-volume.")
    madhab: str | None = Field(default=None, description="Madhab when applicable.")
    language: str = Field(default="Arabic", description="Primary language of the text.")
    blurb: str | None = Field(default=None, description="One-sentence editorial summary, if any.")
