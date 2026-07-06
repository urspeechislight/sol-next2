"""Pydantic DTO for a resolved Qur'an citation anchored in a page's text.

Served from the citation sidecar (``data/citations.db``, built read-only over
the immutable corpus). Only the auto-linkable set reaches the reader: a citation
whose surah is named unambiguously, whose aya is in range, and whose adjacent
quoted text was confirmed to be that verse. ``offset``/``length`` index into the
page's Arabic text so the reader can wrap the printed citation in place without
rewriting it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from backend.core.constants import QURAN__SURAH_COUNT
from backend.models._base import FrozenModel

CitationMatch = Literal["exact", "short", "neighbor"]


class Citation(FrozenModel):
    """One verse-verified Qur'an citation located in a page's Arabic text."""

    offset: int = Field(ge=0, description="Character offset of the marker in the page text.")
    length: int = Field(ge=1, description="Character length of the citation marker.")
    surah: int = Field(ge=1, le=QURAN__SURAH_COUNT, description="Resolved surah number.")
    aya_start: int = Field(ge=1, description="First aya of the reference.")
    aya_end: int = Field(ge=1, description="Last aya (equals aya_start for a single verse).")
    verse_match: CitationMatch = Field(
        description="How the quoted text was confirmed against the cited verse."
    )
