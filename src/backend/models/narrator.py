"""Pydantic DTOs for the narrator registry: rijal entries and enriched persons.

These mirror the served columns of ``data/registry.db`` (built by
``scripts/build_registry.py`` from sol-next's corpus) and are the SSOT the
frontend's narrator types bind to. The reader links isnad text to these
records by name; the graph screens browse them directly. ``PersonEntry`` is the
authoritative per-narrator identity (junk-excluded, over-merge-split,
death-reconciled) built by ``backend.build.authority``; ``RijalEntry`` remains
the raw per-source-entry view.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import Field, field_validator

from backend.models._base import FrozenModel


class NarratorBase(FrozenModel):
    """Identity fields shared by a raw rijal entry and an enriched person.

    Only the fields whose semantics are identical on both sides live here; the
    teacher/student count fields stay per-model because they mean different
    things (counts recorded on one source entry vs. the union across the
    entries merged into one identity).
    """

    full_name: str = Field(description="Full name in Arabic.")
    kunya: str = Field(default="", description="Teknonym (Abu/Umm ...), if recorded.")
    nisba: str = Field(default="", description="Attributive name (tribe/place), if recorded.")
    tradition: str = Field(default="", description="Sunni / shia / both, when classified.")


class RijalEntry(NarratorBase):
    """One narrator in the rijal registry (reliability-graded)."""

    id: int = Field(ge=0, description="Stable corpus index, also the detail-route key.")
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


class PersonEntry(NarratorBase):
    """An authoritative narrator identity, cross-checked across its source entries."""

    person_id: int = Field(ge=0, description="Stable person identity id + detail-route key.")
    name_variants: str = Field(default="", description="Distinct spellings, pipe-separated.")
    birth_year: int | None = Field(default=None, description="Birth year, Hijri, when known.")
    death_year: int | None = Field(default=None, description="Reconciled Hijri death year.")
    death_conflict: bool = Field(default=False, description="Sources disagree on the death year.")
    stance: str = Field(default="", description="Position vis-a-vis ahlulbayt, when evaluated.")
    reliability: list[str] = Field(
        default_factory=list, description="Per-evaluator reliability grades (evaluator=term)."
    )
    places: str = Field(default="", description="Associated places, pipe-separated.")
    source_books: str = Field(default="", description="Source works, pipe-separated.")
    n_sources: int = Field(ge=0, description="Raw corpus entries merged into this identity.")
    teacher_count: int = Field(ge=0, description="Distinct recorded teachers (person_edge).")
    student_count: int = Field(ge=0, description="Distinct recorded students (person_edge).")
    event_count: int = Field(ge=0, description="Historical events attributed to this person.")
    bio: str = Field(default="", description="Longest available biographical snippet.")
    confidence: str = Field(default="medium", description="Record confidence (high/medium).")

    @field_validator("reliability", mode="before")
    @classmethod
    def _parse_reliability(cls, value: Any) -> Any:
        """Decode the stored JSON array of reliability grades into a list."""
        return json.loads(value) if isinstance(value, str) else value


class PersonEdge(FrozenModel):
    """A teacher or student relation of a person, linked to a person id when known."""

    relation: str = Field(description="'teacher' or 'student'.")
    name: str = Field(description="The related narrator's name as recorded.")
    other_person_id: int | None = Field(
        default=None, description="Resolved person id of the relation, or null when unlinked."
    )


class PersonEvent(FrozenModel):
    """A historical event attributed to a person."""

    event: str = Field(default="", description="Event name (battle, conquest, ...).")
    event_type: str = Field(default="", description="Event category (BATTLE, CONQUEST, ...).")
    year_ah: int | None = Field(default=None, description="Hijri year of the event, when dated.")
    role: str = Field(default="", description="Marker keyword linking person to event.")
