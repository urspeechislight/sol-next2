"""Pydantic DTOs for the narrator registry served from ``data/registry.db``.

These mirror the served columns of the artifact built by
``scripts/build_registry.py`` from sol-next3's Postgres narrator store and are
the SSOT the frontend's narrator types bind to. ``NarratorEntry`` is the list
row; ``NarratorDetail`` adds the per-narrator aliases, grades, stances, and
tarjama claims; ``NarratorGraph`` carries the teacher/student relation
expansion the graph screens browse.
"""

from __future__ import annotations

from pydantic import Field

from backend.models._base import FrozenModel


class NarratorEntry(FrozenModel):
    """One narrator in the registry list row."""

    id: int = Field(ge=1, description="Narrator id, also the detail-route key.")
    primary_name_ar: str = Field(description="Primary name in Arabic.")
    primary_name_en: str = Field(default="", description="Primary name in English, when recorded.")
    kunya: str = Field(default="", description="Teknonym (Abu/Umm ...), when recorded.")
    nisba: str = Field(default="", description="Attributive name (tribe/place), when recorded.")
    tradition: str = Field(default="", description="School of law (imami / shafii / ...).")
    birth_year_ah: int | None = Field(default=None, description="Birth year, Hijri, when known.")
    death_year_ah: int | None = Field(default=None, description="Death year, Hijri, when known.")
    death_year_ce: str = Field(default="", description="Death year, Common Era, as recorded.")
    tabaqa: str = Field(default="", description="Generation class (من التاسعة, ...).")
    living_city: str = Field(default="", description="City the narrator lived in, when recorded.")
    death_place: str = Field(default="", description="Place of death, when recorded.")
    category: str = Field(default="clean", description="Data-quality class (clean, long_entry).")
    alias_count: int = Field(ge=0, description="Recorded name variants (narrator_alias).")
    teacher_count: int = Field(ge=0, description="Distinct recorded teachers (narrator_edge).")
    student_count: int = Field(ge=0, description="Distinct recorded students (narrator_edge).")


class NarratorAliasOut(FrozenModel):
    """One recorded name variant of a narrator."""

    name_ar: str = Field(description="The variant spelling, Arabic, as recorded.")
    name_role: str = Field(default="", description="primary / variant / kunya / nisba.")
    source_label: str = Field(default="", description="Human label of the source work.")


class NarratorGradeOut(FrozenModel):
    """One reliability grade issued by a critic, with its provenance."""

    term: str = Field(description="Verdict term as recorded (ثقة, مجهول, ...).")
    tier: str = Field(default="", description="Normalized tier (thiqa, ...).")
    evaluator: str = Field(default="", description="Critic who issued the verdict.")
    source_label: str = Field(default="", description="Human label of the source work.")
    source_book: str = Field(default="", description="Source book id in the extraction record.")
    source_locator: str = Field(default="", description="Locator (page/entry) in the source book.")


class NarratorDetail(NarratorEntry):
    """One narrator with its full served record: aliases, claims, and relations."""

    aliases: list[NarratorAliasOut] = Field(default_factory=list, description="Name variants.")
    grades: list[NarratorGradeOut] = Field(default_factory=list, description="Reliability grades.")
    stances: list[dict[str, str]] = Field(
        default_factory=list,
        description="Stance claims ({predicate, value_text} pairs).",
    )
    tarjama: list[str] = Field(
        default_factory=list, description="Biographical snippets (TARJAMA claim texts)."
    )


class NarratorGraphNode(FrozenModel):
    """One node in an isnad relation expansion."""

    id: int = Field(ge=1, description="Narrator id.")
    primary_name_ar: str = Field(description="Primary name in Arabic.")
    primary_name_en: str = Field(default="", description="Primary name in English, when recorded.")
    death_year_ah: int | None = Field(default=None, description="Death year, Hijri, when known.")
    depth: int = Field(ge=0, description="Hops from the root narrator (0 for the root).")


class NarratorGraphEdge(FrozenModel):
    """One teacher→student relation edge in the expansion."""

    from_id: int = Field(ge=1, description="Teacher narrator id.")
    to_id: int = Field(ge=1, description="Student narrator id.")
    source_label: str = Field(description="Human label of the source the edge was read from.")


class NarratorGraph(FrozenModel):
    """A breadth-limited teacher or student expansion around one narrator."""

    root_id: int = Field(ge=1, description="The narrator the expansion is rooted at.")
    direction: str = Field(description="students (descendants) or teachers (ancestors).")
    depth: int = Field(ge=1, description="Maximum hops from the root actually expanded.")
    nodes: list[NarratorGraphNode] = Field(description="The root plus every reached narrator.")
    edges: list[NarratorGraphEdge] = Field(description="The traversed relations.")
    truncated: bool = Field(description="True when the node cap stopped the expansion early.")
