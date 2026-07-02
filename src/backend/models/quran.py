"""Pydantic DTO for a single Qurʾān verse (ayah)."""

from __future__ import annotations

from pydantic import Field

from backend.models._base import FrozenModel


class Ayah(FrozenModel):
    """One Qurʾān verse, resolved from a surah:ayah reference.

    ``text_ar`` carries the diacritized recitation text; ``text_plain`` is the
    same verse with vowel marks stripped, so a reader sees both the pointed and
    the bare forms that corpus quotations may use. The diacritic-insensitive
    matching against book content is handled by the search FTS tokenizer, so
    either form locates the same passages.
    """

    surah: int = Field(ge=1, description="Surah number.")
    ayah: int = Field(ge=1, description="Ayah number within the surah.")
    verse_count: int = Field(ge=1, description="Total ayat in the surah.")
    text_ar: str = Field(description="Verse text with diacritics.")
    text_plain: str = Field(description="Verse text with diacritics stripped.")
    text_en: str | None = Field(default=None, description="English rendering, if available.")
