"""Pydantic DTOs for the Daily editorial: verse, hadith, and book pick.

``DailyPool`` is the shape of ``data/daily.json``: parallel pools of curated
entries that the repository rotates through by calendar day. ``Daily`` is the
served selection: one entry from each pool. The verse pool stores only the
surah:ayah reference plus its tafsir excerpts; the scripture text is composed
at serve time from the Qurʾān repository, the single source of Qurʾān text.
Deep-link fields (``urn`` + ``page``) are nullable throughout: a citation
whose work is not held by the catalogue is cited textually, never linked to a
fabricated target.
"""

from __future__ import annotations

from pydantic import Field

from backend.core.constants import QURAN__SURAH_COUNT
from backend.models._base import FrozenModel
from backend.models.grades import HadithGrade


class Tafsir(FrozenModel):
    """One tafsir excerpt attached to the verse of the day."""

    book: str
    book_ar: str
    author: str
    urn: str | None = None
    page: int | None = Field(default=None, ge=1)
    excerpt_en: str
    excerpt_ar: str


class VersePick(FrozenModel):
    """A pool entry for the verse of the day: the reference plus its curation."""

    surah_n: int = Field(ge=1, le=QURAN__SURAH_COUNT)
    ayah_n: int = Field(ge=1)
    tafsirs: list[Tafsir]


class Verse(VersePick):
    """Verse of the day as served: the pool curation plus the canonical text."""

    ayah_ar: str
    ayah_en: str | None = None


class HadithSource(FrozenModel):
    """The originating book of a hadith of the day."""

    book: str
    book_ar: str
    n: str = Field(
        description="Report number within the source (often non-integer like '1/34/h.1')."
    )
    urn: str | None = None
    page: int | None = Field(default=None, ge=1)
    sect: str


class HadithParallel(HadithSource):
    """A parallel narration in another collection."""


class DailyHadith(FrozenModel):
    """Hadith of the day with source + parallels + grade."""

    matn_ar: str
    matn_en: str
    isnad_ar: str
    source: HadithSource
    parallels: list[HadithParallel]
    grade: HadithGrade
    grade_label: str
    note: str


class OpenTo(FrozenModel):
    """Where to open the recommended book."""

    page: int = Field(ge=1)
    chapter_en: str


class DailyBookPick(FrozenModel):
    """The 'book of the day' pick."""

    urn: str
    rationale: str
    open_to: OpenTo


class Daily(FrozenModel):
    """Top-level Daily payload: today's selection from each pool."""

    verse: Verse
    hadith: DailyHadith
    book: DailyBookPick


class DailyPool(FrozenModel):
    """The curated pools behind the Daily rotation (``data/daily.json``)."""

    verses: list[VersePick] = Field(min_length=1)
    hadiths: list[DailyHadith] = Field(min_length=1)
    books: list[DailyBookPick] = Field(min_length=1)
