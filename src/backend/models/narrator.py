"""Pydantic DTOs for the narrator registry: rijal + canonical entries.

These mirror the served columns of ``data/registry.db`` (built by
``scripts/build_registry.py`` from sol-next's corpus) and are the SSOT the
frontend's narrator types bind to. The reader links isnad text to these
records by name; the graph screens browse them directly.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RijalEntry(BaseModel):
    """One narrator in the rijal registry (reliability-graded)."""

    model_config = ConfigDict(frozen=True)

    id: int = Field(ge=0, description="Stable corpus index, also the detail-route key.")
    full_name: str = Field(description="Full name in Arabic.")
    kunya: str = Field(default="", description="Teknonym (Abu/Umm ...), if recorded.")
    nisba: str = Field(default="", description="Attributive name (tribe/place), if recorded.")
    tradition: str = Field(default="", description="Sunni / shia / both, when classified.")
    death_year: str = Field(default="", description="Death year as recorded (Hijri, free-form).")
    birth_year: str = Field(default="", description="Birth year as recorded (Hijri, free-form).")
    category: str = Field(default="clean", description="Data-quality class (clean, editorial).")
    teacher_count: int = Field(ge=0, description="Number of recorded teachers.")
    student_count: int = Field(ge=0, description="Number of recorded students.")
    reliability_term: str = Field(default="", description="Primary reliability term (thiqa, ...).")
    reliability_grade: str = Field(default="", description="Numeric reliability grade, as text.")
    evaluator: str = Field(default="", description="Critic who issued the reliability term.")
    source_label: str = Field(default="", description="Human label of the source work + volume.")
    book_path: str = Field(default="", description="Relative path of the source corpus file.")


class CanonicalEntry(BaseModel):
    """A canonicalized person, merging one identity across sources."""

    model_config = ConfigDict(frozen=True)

    canonical_id: int = Field(ge=0, description="Stable canonical identity id + detail-route key.")
    full_name: str = Field(description="Full name in Arabic.")
    kunya: str = Field(default="", description="Teknonym, if recorded.")
    nisba: str = Field(default="", description="Attributive name, if recorded.")
    tradition: str = Field(default="", description="Sunni / shia / both, when classified.")
    death_year: int | None = Field(default=None, description="Death year, Hijri, when known.")
    birth_year: int | None = Field(default=None, description="Birth year, Hijri, when known.")
    entry_count: int = Field(ge=0, description="Raw corpus entries merged into this identity.")
    source_count: int = Field(ge=0, description="Distinct source works contributing entries.")
    teacher_count: int = Field(ge=0, description="Union of recorded teachers across entries.")
    student_count: int = Field(ge=0, description="Union of recorded students across entries.")
    merge_confidence: float | None = Field(
        default=None, description="Merge confidence in 0..1, or null when unscored."
    )
