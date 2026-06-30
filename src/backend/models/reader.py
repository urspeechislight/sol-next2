"""Pydantic DTOs for the reader screens: TOC + page content."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.models.grades import HadithGrade


class TocEntry(BaseModel):
    """One row in a book's table of contents."""

    model_config = ConfigDict(frozen=True)

    page: int = Field(ge=1, description="Page number where this section begins.")
    title: str = Field(description="Arabic section title.")
    title_en: str | None = Field(default=None, description="English section title, if translated.")
    active: bool = Field(
        default=False, description="Whether this is the section currently being read."
    )


class Toc(BaseModel):
    """The full table of contents for one book."""

    model_config = ConfigDict(frozen=True)

    book_urn: str = Field(description="URN of the book this TOC belongs to.")
    entries: list[TocEntry] = Field(description="Ordered TOC rows.")


class Narrator(BaseModel):
    """One narrator in an isnad."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Name in romanized form.")
    name_ar: str = Field(description="Name in Arabic.")
    role: str = Field(description="Role / position in the chain (companion, transmitter, ...).")
    grade: str = Field(description="Biographical evaluation (Trustworthy, Reliable, ...).")
    d: int | None = Field(default=None, description="Death year, Hijri.")


class CrossRef(BaseModel):
    """Pointer to a parallel narration in another collection."""

    model_config = ConfigDict(frozen=True)

    book: str = Field(description="Source book (English transliteration).")
    book_ar: str = Field(description="Source book (Arabic).")
    chapter: str = Field(description="Chapter or volume reference.")
    page: int | None = Field(default=None, description="Page number in the source book.")


class Hadith(BaseModel):
    """One hadith record: isnad + matn + narrators + cross-references."""

    model_config = ConfigDict(frozen=True)

    n: int = Field(ge=1, description="Sequence number on the page.")
    isnad_ar: str = Field(description="Chain of transmission in Arabic.")
    matn_ar: str = Field(description="Body of the hadith in Arabic.")
    matn_en: str | None = Field(default=None, description="English translation of the matn.")
    narrators: list[Narrator] = Field(description="Narrators in the chain.")
    grade: HadithGrade | None = Field(
        default=None,
        description=(
            "Authenticity grade. None when the page is raw corpus text that the "
            "pipeline has not yet graded; the UI hides the grade pill in that case."
        ),
    )
    cross_refs: list[CrossRef] = Field(default_factory=list, description="Parallel narrations.")


class BookPage(BaseModel):
    """One book page: hadiths under a chapter + section heading."""

    model_config = ConfigDict(frozen=True)

    page_number: int = Field(ge=1)
    total_pages: int = Field(ge=1)
    chapter_title: str
    chapter_title_en: str | None = None
    section_title: str
    section_title_en: str | None = None
    hadiths: list[Hadith]


class BookSearchMatch(BaseModel):
    """One in-book search hit: the page and a short Arabic excerpt."""

    model_config = ConfigDict(frozen=True)

    page: int = Field(ge=1, description="Page the match occurs on.")
    snippet: str = Field(description="Excerpt of the matching unit (Arabic).")
