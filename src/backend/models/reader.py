"""Pydantic DTOs for the reader screens: TOC + page content."""

from __future__ import annotations

from pydantic import Field

from backend.models._base import FrozenModel
from backend.models.grades import HadithGrade


class TocEntry(FrozenModel):
    """One row in a book's table of contents."""

    page: int = Field(ge=1, description="Page number where this section begins.")
    title: str = Field(description="Arabic section title.")
    title_en: str | None = Field(default=None, description="English section title, if translated.")
    active: bool = Field(
        default=False, description="Whether this is the section currently being read."
    )


class Toc(FrozenModel):
    """The full table of contents for one book."""

    book_urn: str = Field(description="URN of the book this TOC belongs to.")
    entries: list[TocEntry] = Field(description="Ordered TOC rows.")


class Footnote(FrozenModel):
    """One entry in a page's footnote apparatus: the editor's notes as printed.

    The apparatus is page-local, mirroring the print edition: an entry is
    served with the page whose foot it is printed on. Roughly 1% of corpus
    markers reference an entry printed on the neighboring page; those entries
    still appear on their own page, exactly as the edition prints them.
    """

    marker: str | None = Field(
        default=None,
        description=(
            "Entry number as printed in the edition ('1', '2', ...). None for "
            "unnumbered note text: a free-form editorial block, or the "
            "continuation of the previous page's entry in continuously "
            "numbered editions. The block split is lossless, so None never "
            "means a parse failure."
        ),
    )
    text: str = Field(description="Arabic note text as printed.")


class Narrator(FrozenModel):
    """One narrator in an isnad."""

    name: str = Field(description="Name in romanized form.")
    name_ar: str = Field(description="Name in Arabic.")
    role: str = Field(description="Role / position in the chain (companion, transmitter, ...).")
    grade: str = Field(description="Biographical evaluation (Trustworthy, Reliable, ...).")
    d: int | None = Field(default=None, description="Death year, Hijri.")
    narrator_id: int | None = Field(
        default=None,
        description=(
            "Registry link: id in /api/narrators, resolved at build time by "
            "normalized-name match. None when the registry does not know this "
            "narrator; the reader shows the name unlinked rather than guessing."
        ),
    )


class CrossRef(FrozenModel):
    """Pointer to a parallel narration in another collection."""

    book: str = Field(description="Source book (English transliteration).")
    book_ar: str = Field(description="Source book (Arabic).")
    chapter: str = Field(description="Chapter or volume reference.")
    page: int | None = Field(default=None, description="Page number in the source book.")


class Hadith(FrozenModel):
    """One hadith record: isnad + matn + narrators + cross-references."""

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
    cross_refs: list[CrossRef] = Field(
        default_factory=list[CrossRef], description="Parallel narrations."
    )


class BookPage(FrozenModel):
    """One book page: parsed hadiths, or raw page text when none are parsed yet."""

    page_number: int = Field(ge=1)
    total_pages: int = Field(ge=1)
    chapter_title: str
    chapter_title_en: str | None = None
    section_title: str
    section_title_en: str | None = None
    hadiths: list[Hadith]
    text_ar: str | None = Field(
        default=None,
        description=(
            "Raw page text in Arabic, present when the pipeline has not parsed the "
            "page into structured hadiths. Mutually exclusive with a populated "
            "hadiths list; never both."
        ),
    )
    text_en: str | None = Field(
        default=None,
        description=(
            "English translation of the raw page text, paired with text_ar. None "
            "until the pipeline emits a translation for the page; the reader shows a "
            "labelled preview in that case and this real text the moment it arrives."
        ),
    )
    footnotes: list[Footnote] = Field(
        default_factory=list[Footnote],
        description=(
            "The page's footnote apparatus in printed order; empty when the "
            "source row carries no footnote block. Served for raw and "
            "hadith-parsed pages alike: the notes annotate the printed page, "
            "not the extraction."
        ),
    )


class BookSearchMatch(FrozenModel):
    """One in-book search hit: the page and a short Arabic excerpt."""

    page: int = Field(ge=1, description="Page the match occurs on.")
    snippet: str = Field(description="Excerpt of the matching unit (Arabic).")
