"""Pydantic DTOs for the Daily editorial: verse, hadith, book pick, rotation."""

from __future__ import annotations

from pydantic import Field

from backend.models._base import FrozenModel
from backend.models.grades import HadithGrade


class DailyDate(FrozenModel):
    """Date display values for the editorial header."""

    hijri: str
    hijri_short: str
    gregorian: str


class Tafsir(FrozenModel):
    """One tafsir excerpt attached to the verse of the day."""

    book: str
    book_ar: str
    author: str
    urn: str
    excerpt_en: str
    excerpt_ar: str


class Verse(FrozenModel):
    """Verse of the day with one or more tafsir excerpts."""

    surah: str
    surah_ar: str
    surah_n: int = Field(ge=1, le=114)
    ayah_n: int = Field(ge=1)
    ayah_ar: str
    ayah_en: str
    tafsirs: list[Tafsir]


class HadithSource(FrozenModel):
    """The originating book of a hadith of the day."""

    book: str
    book_ar: str
    n: str = Field(
        description="Report number within the source (often non-integer like '1/34/h.1')."
    )
    urn: str | None = None
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
    """Top-level Daily payload."""

    date: DailyDate
    verse: Verse
    hadith: DailyHadith
    book: DailyBookPick
    rotation: list[str]
