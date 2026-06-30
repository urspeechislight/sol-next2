"""Pydantic DTOs for the Daily editorial: verse, hadith, book pick, rotation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.models.grades import HadithGrade


class DailyDate(BaseModel):
    """Date display values for the editorial header."""

    model_config = ConfigDict(frozen=True)

    hijri: str
    hijri_short: str
    gregorian: str


class Tafsir(BaseModel):
    """One tafsir excerpt attached to the verse of the day."""

    model_config = ConfigDict(frozen=True)

    book: str
    book_ar: str
    author: str
    urn: str
    excerpt_en: str
    excerpt_ar: str


class Verse(BaseModel):
    """Verse of the day with one or more tafsir excerpts."""

    model_config = ConfigDict(frozen=True)

    surah: str
    surah_ar: str
    surah_n: int = Field(ge=1, le=114)
    ayah_n: int = Field(ge=1)
    ayah_ar: str
    ayah_en: str
    tafsirs: list[Tafsir]


class HadithSource(BaseModel):
    """The originating book of a hadith of the day."""

    model_config = ConfigDict(frozen=True)

    book: str
    book_ar: str
    n: str = Field(
        description="Report number within the source (often non-integer like '1/34/h.1')."
    )
    urn: str | None = None
    sect: str


class HadithParallel(HadithSource):
    """A parallel narration in another collection."""


class DailyHadith(BaseModel):
    """Hadith of the day with source + parallels + grade."""

    model_config = ConfigDict(frozen=True)

    matn_ar: str
    matn_en: str
    isnad_ar: str
    source: HadithSource
    parallels: list[HadithParallel]
    grade: HadithGrade
    grade_label: str
    note: str


class OpenTo(BaseModel):
    """Where to open the recommended book."""

    model_config = ConfigDict(frozen=True)

    page: int = Field(ge=1)
    chapter_en: str


class DailyBookPick(BaseModel):
    """The 'book of the day' pick."""

    model_config = ConfigDict(frozen=True)

    urn: str
    rationale: str
    open_to: OpenTo


class Daily(BaseModel):
    """Top-level Daily payload."""

    model_config = ConfigDict(frozen=True)

    date: DailyDate
    verse: Verse
    hadith: DailyHadith
    book: DailyBookPick
    rotation: list[str]
