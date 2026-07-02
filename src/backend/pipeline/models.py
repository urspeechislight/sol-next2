"""Core data types for the ported pipeline — the phase 2-3 contract.

One Span type, filled progressively: behavior + hierarchy by segment (phase 2),
entities + units by extract (phase 3). Never rewrapped to signal that more data
has been added; callers check ``span.units is not None``.

Ported from sol-next's src/models/__init__.py with the phase-5 surface (Edge,
ChainGrade, HadithGrade) and the extract-phase create_entity factory deferred
to their own milestones, and view-layer to_dict serialization dropped (the
manuscript artifact writer maps these models to its own row shapes). The
manuscript page type is named ManuscriptPage to avoid clashing with the
unrelated pagination envelope Page in backend.models.pagination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from backend.core.constants import HADITH__ENTITY_PERSON

if TYPE_CHECKING:
    from backend.pipeline.config import Config


@dataclass
class Pattern:
    """A surface-level pattern detected in a span's text.

    Detected by segment using the regex rules in config/sol.yaml. Each pattern
    carries the slice of text it matched and its character offsets so later
    phases can build evidence anchors from it.
    """

    pattern_id: str
    matched_text: str
    char_start: int
    char_end: int
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])


@dataclass
class HierarchyPath:
    """The document position of a span: which kitab / bab / fasl it sits in.

    Assigned by segment via the hierarchy FSM trackers. ``path`` holds the
    human-readable titles, ``path_ids`` their stable ids, and ``depth`` the
    nesting level.
    """

    path: list[str]
    path_ids: list[str]
    depth: int


@dataclass
class EvidenceAnchor:
    """Exact source location where an entity was found.

    Lets a reader trace any extracted entity back to the span, page, and
    surrounding context it came from.
    """

    span_id: str
    page_start: int
    page_end: int
    hierarchy: HierarchyPath
    context_before: str
    context_after: str


@dataclass
class ExtractionProvenance:
    """How an entity was extracted: which extractor, which phase, which patterns."""

    extractor_id: str
    phase: int
    pattern_ids: list[str]


@dataclass
class Entity:
    """An extracted entity from a span.

    Assigned by extract via behavior-gated extractors. PERSON entities carry a
    ``role_in_context`` in metadata (narrator, teacher, student, ...) and, once
    the registry linker resolves them, a rijal id.
    """

    entity_id: str
    entity_type: str
    text: str
    char_start: int
    char_end: int
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])
    provenance: ExtractionProvenance | None = None
    evidence: EvidenceAnchor | None = None
    confidence: float | None = None


@dataclass
class Unit:
    """One atomic semantic unit — a single coherent thought.

    Assigned by extract via behavior-specific atomicizers. A HADITH_TRANSMISSION
    span splits into an ISNAD_UNIT (chain of narrators) and a MATN_UNIT (the
    reported text); other behaviors yield a single whole-span unit.
    """

    unit_id: str
    text_ar: str
    unit_type: str
    behavior: str
    span_id: str
    page_start: int
    page_end: int
    hierarchy: HierarchyPath
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])


@dataclass
class Span:
    """A structural segment of a manuscript page.

    One type, used from phase 2 onward. Fields fill in progressively: patterns
    and behavior and hierarchy by segment; entities and units by extract. A span
    whose units/entities are still None has not been through extract.
    """

    span_id: str
    text: str
    page_start: int
    page_end: int
    span_type: str
    patterns: list[Pattern] = field(default_factory=list[Pattern])
    behavior: str | None = None
    hierarchy: HierarchyPath | None = None
    entities: list[Entity] | None = None
    units: list[Unit] | None = None
    footnote_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def patterns_by_id(self, *pattern_ids: str) -> list[Pattern]:
        """Return this span's patterns whose id is in ``pattern_ids``, sorted by offset.

        Pass one id for the common single-pattern case, or several for behaviors
        that consume a small set (e.g. the name-end markers in a biography).
        """
        target = frozenset(pattern_ids)
        return sorted(
            (p for p in self.patterns if p.pattern_id in target),
            key=lambda p: p.char_start,
        )

    def persons_by_role(self, *roles: str) -> list[Entity]:
        """Return PERSON entities on this span, optionally filtered by role.

        With no roles, returns every PERSON entity; otherwise only those whose
        ``role_in_context`` metadata is in ``roles``. Order is preserved.
        """
        if not self.entities:
            return []
        if not roles:
            return [e for e in self.entities if e.entity_type == HADITH__ENTITY_PERSON]
        target = frozenset(roles)
        return [
            e
            for e in self.entities
            if e.entity_type == HADITH__ENTITY_PERSON
            and (e.metadata or {}).get("role_in_context") in target
        ]


@dataclass
class ManuscriptPage:
    """A single page from an ingested manuscript.

    Produced from sol-next2's reader page rows and fed to segment. ``footnote``
    carries the page's footnote block (some extractors scan it); ``is_content``
    is false for frontmatter pages skipped before the content start.
    """

    page_number: int
    page_name: str
    text: str
    footnote: str | None = None
    is_content: bool = True


class DegradedMode(Enum):
    """Quality compromises the pipeline tracks explicitly rather than silently.

    Only the modes current phases can actually enter carry members; each
    future phase (NER validation, rijal linking, enrich, graph) brings its
    modes back with it.
    """

    ISNAD_SPLIT_FALLBACK = auto()


@dataclass
class ValidationIssue:
    """A recorded quality compromise with the context needed to investigate it."""

    phase: int
    issue_type: DegradedMode
    span_id: str | None
    message: str
    severity: str


@dataclass
class Manuscript:
    """The complete processed state of one manuscript, passed between phases.

    Phases mutate it in place: segment fills ``spans``; extract fills each
    span's entities and units. ``degraded_modes`` and ``validation_issues`` let
    the pipeline fail loud when quality drops below the configured budget.
    """

    work_id: str
    manifestation_id: str
    pages: list[ManuscriptPage] = field(default_factory=list[ManuscriptPage])
    spans: list[Span] = field(default_factory=list[Span])
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])
    degraded_modes: set[DegradedMode] = field(default_factory=set[DegradedMode])
    validation_issues: list[ValidationIssue] = field(default_factory=list[ValidationIssue])

    @property
    def units(self) -> list[Unit]:
        """Every atomic unit across all spans, in span then unit order."""
        return [u for s in self.spans if s.units for u in s.units]

    @property
    def entities(self) -> list[Entity]:
        """Every entity across all spans, in span then entity order."""
        return [e for s in self.spans if s.entities for e in s.entities]


def create_entity(
    *,
    entity_type: str,
    text: str,
    char_start: int,
    char_end: int,
    span: Span,
    extractor_id: str,
    config: Config,
    phase: int,
    metadata: dict[str, Any] | None = None,
    confidence: float | None = None,
    text_source: str | None = None,
) -> Entity:
    """Factory: an Entity with automatic provenance and evidence anchoring.

    Builds the EvidenceAnchor from the span's location (context window sized by
    config.thresholds.evidence_context_chars) and the ExtractionProvenance
    from the span's detected patterns. The entity_id is left empty; the calling
    phase assigns ids scoped to the producing span. Keyword-only because the
    call sites read better naming every field than positionally threading
    eleven values.
    """
    context_chars = config.thresholds.evidence_context_chars
    source_text = text_source if text_source is not None else span.text
    context_before = source_text[max(0, char_start - context_chars) : char_start]
    context_after = source_text[char_end : char_end + context_chars]
    evidence = EvidenceAnchor(
        span_id=span.span_id,
        page_start=span.page_start,
        page_end=span.page_end,
        hierarchy=span.hierarchy or HierarchyPath(path=[], path_ids=[], depth=0),
        context_before=context_before,
        context_after=context_after,
    )
    provenance = ExtractionProvenance(
        extractor_id=extractor_id,
        phase=phase,
        pattern_ids=[pattern.pattern_id for pattern in span.patterns],
    )
    return Entity(
        entity_id="",
        entity_type=entity_type,
        text=text,
        char_start=char_start,
        char_end=char_end,
        metadata=metadata or {},
        provenance=provenance,
        evidence=evidence,
        confidence=confidence,
    )
