"""Phase 3: EXTRACT.

Input: a Manuscript whose spans carry behavior + hierarchy from Phase 2.
Output: the same Manuscript with each span's entities and units populated.

For each span, gated by span.behavior: (1) run the registered extractors to
produce Entity objects from the already-detected patterns, assigning entity ids
scoped to the span; (2) atomicize the span into Unit objects via the configured
strategy. A HADITH_TRANSMISSION span also gets its isnad_end computed here so the
sanad/matn split and narrator extraction cap at the matn boundary. A content span
that produces zero units is a bug and raises ExtractError.

Ported from sol-next's src/phases/extract.py; the atomicizer strategies and the
isnad back-reference handling were once shards under the old file-size cap and
now live here with the orchestrator. Back-references ("وبهذا الاسناد") are
recorded as pointer metadata on the referencing span's isnad-bearing unit,
never as copied text or entities: the referenced chain is not on this page,
so materializing it would fabricate page-anchored data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.core.constants import HADITH__UNIT_ISNAD
from backend.core.logging import get_logger
from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.config import Config
from backend.pipeline.contracts import PHASE_CONTRACTS, validate_manuscript_for_phase
from backend.pipeline.errors import ExtractError
from backend.pipeline.extractors import EXTRACTOR_REGISTRY, VALID_ENTITY_TYPES, ExtractorFn
from backend.pipeline.extractors.isnad_boundary import (
    AttributionCues,
    build_attribution_cues,
    find_isnad_bounds,
)
from backend.pipeline.models import (
    DegradedMode,
    Entity,
    HierarchyPath,
    Manuscript,
    Span,
    Unit,
    ValidationIssue,
)
from backend.pipeline.text import split_footnote_entries, strip_footnote_markers
from backend.pipeline.vocab import (
    HADITH__ENTITY_ID_FORMAT,
    HADITH__PATTERN_ATTRIBUTION,
    HADITH__PATTERN_NUMBERED_ENTRY,
    HADITH__STRATEGY_SANAD_MATN,
    HADITH__STRATEGY_WHOLE_SPAN,
    HADITH__UNIT_FOOTNOTE,
    HADITH__UNIT_ID_FORMAT,
)

_logger = get_logger("shia-library.pipeline.extract")
_DEGRADED_SEVERITY_INFO = "info"
_ENTRY_NUMBER_DIGITS_REGEX: CompiledPattern = cached_compile(r"[0-9٠-٩]+")


def _leading_entry_number(span: Span) -> int | None:
    """The printed ordinal, when the span opens with a NUMBERED_ENTRY marker.

    The edition's own numbering is the citable identity of the entry and the
    ground truth an entry-sequence audit checks extraction completeness
    against, so it is materialized as a typed field instead of staying buried
    in the marker text. Only a marker with nothing but whitespace before it
    counts: a number mid-span is content. ``int`` reads Arabic-Indic digits
    (٢) as well as Western ones.
    """
    for marker in span.patterns_by_id(HADITH__PATTERN_NUMBERED_ENTRY):
        if span.text[: marker.char_start].strip():
            continue
        digits = _ENTRY_NUMBER_DIGITS_REGEX.search(marker.matched_text)
        if digits is None:
            return None
        return int(digits.group())
    return None


@dataclass
class _ExtractRun:
    """Shared state for one extract pass: the manuscript, config, registry, cues."""

    manuscript: Manuscript
    config: Config
    registry: dict[str, list[ExtractorFn]]
    cues: AttributionCues


def extract(manuscript: Manuscript, config: Config) -> Manuscript:
    """Extract entities and atomicize spans into units.

    Validates atomicizer coverage, then for each span runs its behavior's
    extractors, assigns entity ids, atomicizes the span into units, and appends a
    FOOTNOTE_UNIT per footnote entry. Isnad back-references are resolved last.

    Raises ExtractError when a behavior lacks an atomicizer rule, an extractor or
    strategy is unknown, an entity type is invalid, or a content span yields zero
    units.
    """
    validate_manuscript_for_phase(manuscript, "extract")
    _validate_atomicizer_coverage(manuscript, config)
    run = _ExtractRun(
        manuscript=manuscript,
        config=config,
        registry=_build_extractor_registry(config.extractors),
        cues=build_attribution_cues(config),
    )
    unit_counter = 0
    for span in manuscript.spans:
        unit_counter = _extract_span(span, run, unit_counter)
    _resolve_isnad_back_references(manuscript)
    _logger.info(
        "extract_done",
        manifestation_id=manuscript.manifestation_id,
        spans=len(manuscript.spans),
        units=len(manuscript.units),
        entities=len(manuscript.entities),
    )
    return manuscript


def _extract_span(span: Span, run: _ExtractRun, unit_counter: int) -> int:
    """Extract entities, atomicize, and append footnotes for one span."""
    if span.behavior is None:
        raise ExtractError(f"Span {span.span_id} has no behavior from Phase 2")
    if span.hierarchy is None:
        raise ExtractError(f"Span {span.span_id} has no hierarchy from Phase 2")
    behavior = span.behavior
    hierarchy = span.hierarchy
    config_rule = run.config.atomicizers[behavior]
    strategy = config_rule["strategy"]
    if _needs_isnad_end(strategy, span):
        isnad_start, isnad_end = find_isnad_bounds(
            span,
            run.config.thresholds.isnad_chain_proximity_max,
            run.config.thresholds.isnad_chain_gap_max,
            run.cues,
        )
        span.metadata["isnad_start"] = isnad_start
        span.metadata["isnad_end"] = isnad_end
    entities = _extract_entities(span, run.registry, behavior, run.config)
    for idx, entity in enumerate(entities):
        _validate_entity_type(entity)
        _assign_entity_id(entity, span.span_id, idx)
    units = _atomicize_span(
        span,
        unit_counter,
        strategy,
        config_rule,
        run.manuscript.manifestation_id,
        behavior,
        hierarchy,
    )
    if strategy == HADITH__STRATEGY_SANAD_MATN and len(units) == 1:
        run.manuscript.degraded_modes.add(DegradedMode.ISNAD_SPLIT_FALLBACK)
        run.manuscript.validation_issues.append(
            _degraded_issue(
                DegradedMode.ISNAD_SPLIT_FALLBACK,
                span.span_id,
                "sanad_matn_split produced a single reserve unit",
                _DEGRADED_SEVERITY_INFO,
            )
        )
    unit_counter += len(units)
    if not units and span.text.strip():
        raise ExtractError(f"Span {span.span_id} produced zero units")
    if span.footnote_text:
        for fn_number, fn_text in split_footnote_entries(span.footnote_text):
            fn_unit_id = HADITH__UNIT_ID_FORMAT.format(
                manifestation_id=run.manuscript.manifestation_id, index=unit_counter
            )
            units.append(
                _make_footnote_unit(
                    fn_unit_id, f"({fn_number}) {fn_text}", behavior, hierarchy, span
                )
            )
            unit_counter += 1
    span.entities = entities
    span.units = units
    return unit_counter


def _needs_isnad_end(strategy: object, span: Span) -> bool:
    """Whether this span needs its isnad_end computed before extraction."""
    return strategy == HADITH__STRATEGY_SANAD_MATN or bool(
        span.patterns_by_id(HADITH__PATTERN_ATTRIBUTION)
    )


def _validate_entity_type(entity: Entity) -> None:
    """Raise ExtractError when the entity type is not in the valid set."""
    if entity.entity_type not in VALID_ENTITY_TYPES:
        raise ExtractError(f"Unknown entity_type: {entity.entity_type}")


def _assign_entity_id(entity: Entity, span_id: str, idx: int) -> None:
    """Stamp the entity id scoped to its producing span."""
    entity.entity_id = HADITH__ENTITY_ID_FORMAT.format(span_id=span_id, index=idx)


def _validate_atomicizer_coverage(manuscript: Manuscript, config: Config) -> None:
    """Raise ExtractError when a span's behavior has no atomicizer rule."""
    for span in manuscript.spans:
        behavior = span.behavior
        if behavior is not None and behavior not in config.atomicizers:
            raise ExtractError(f"No atomicizer rule for behavior: {behavior}")


def _build_extractor_registry(
    config_extractors: dict[str, list[str]],
) -> dict[str, list[ExtractorFn]]:
    """Resolve config extractor names to callables; raise on an unknown name."""
    registry: dict[str, list[ExtractorFn]] = {}
    for behavior_id, extractor_names in config_extractors.items():
        callables: list[ExtractorFn] = []
        for name in extractor_names:
            if name not in EXTRACTOR_REGISTRY:
                raise ExtractError(f"Unknown extractor: {name}")
            callables.append(EXTRACTOR_REGISTRY[name])
        registry[behavior_id] = callables
    return registry


def _extract_entities(
    span: Span,
    registry: dict[str, list[ExtractorFn]],
    behavior: str,
    config: Config,
) -> list[Entity]:
    """Run every extractor registered for this behavior and collect entities."""
    entities: list[Entity] = []
    for extractor_fn in registry.get(behavior, []):
        entities.extend(extractor_fn(span, config))
    return entities


def _degraded_issue(
    issue_type: DegradedMode, span_id: str | None, message: str, severity: str
) -> ValidationIssue:
    """Build a ValidationIssue stamped with the extract phase number."""
    return ValidationIssue(
        phase=PHASE_CONTRACTS["extract"].phase_number,
        issue_type=issue_type,
        span_id=span_id,
        message=message,
        severity=severity,
    )


def _atomicize_span(
    span: Span,
    start_index: int,
    strategy: str,
    config_rule: dict[str, Any],
    manifestation_id: str,
    behavior: str,
    hierarchy: HierarchyPath,
) -> list[Unit]:
    """Dispatch the configured atomicizer strategy, raising on an unknown one.

    whole_span emits one unit covering the span; sanad_matn_split emits an
    ISNAD unit + a MATN unit at the precomputed isnad_end, with a whole-span
    reserve unit when the split yields an empty side.
    """
    if strategy == HADITH__STRATEGY_WHOLE_SPAN:
        return _atomicize_whole_span(
            span, start_index, config_rule, manifestation_id, behavior, hierarchy
        )
    if strategy == HADITH__STRATEGY_SANAD_MATN:
        return _atomicize_sanad_matn(
            span, start_index, config_rule, manifestation_id, behavior, hierarchy
        )
    raise ExtractError(f"Unknown atomicizer strategy: {strategy}")


def _text_from_pattern(span: Span, pattern_id: str) -> str:
    """Return the first match of pattern_id, else the full span text.

    When a structural span's content IS the pattern match (e.g. BASMALA), the unit
    text is the matched text rather than the full span, which may carry inter-
    boundary noise.
    """
    for pattern in span.patterns:
        if pattern.pattern_id == pattern_id:
            return pattern.matched_text.strip()
    return span.text.strip()


def _atomicize_whole_span(
    span: Span,
    start_index: int,
    config_rule: dict[str, Any],
    manifestation_id: str,
    behavior: str,
    hierarchy: HierarchyPath,
) -> list[Unit]:
    """One unit covering the whole span; optionally retext from a pattern match."""
    unit_type: str = config_rule["unit_type"]
    unit_id = HADITH__UNIT_ID_FORMAT.format(manifestation_id=manifestation_id, index=start_index)
    unit_metadata: dict[str, Any] = {}
    comments_on = span.metadata.get("comments_on_span_id")
    if comments_on is not None:
        unit_metadata["comments_on_span_id"] = comments_on
    entry_number = _leading_entry_number(span)
    if entry_number is not None:
        unit_metadata["entry_number"] = entry_number
    pattern_id = config_rule.get("use_pattern_text")
    if pattern_id is not None:
        text_ar = _text_from_pattern(span, pattern_id)
        span.text = text_ar
    else:
        text_ar = strip_footnote_markers(span.text)
    return [_unit(span, unit_id, text_ar, unit_type, behavior, hierarchy, metadata=unit_metadata)]


def _atomicize_sanad_matn(
    span: Span,
    start_index: int,
    config_rule: dict[str, Any],
    manifestation_id: str,
    behavior: str,
    hierarchy: HierarchyPath,
) -> list[Unit]:
    """Split the span into ISNAD + MATN units at isnad_end, else one reserve unit.

    The isnad unit's text starts at isnad_start: the citation head a compilation
    prints before the chain (hadith ordinal + source works) is bibliography, not
    transmission, so it stays out of the unit text and rides in the unit's
    ``citation_head`` metadata instead. The span text itself is untouched, so
    the reader still renders the line as printed. When the split produces an
    empty isnad or matn side, the configured reserve unit type covers the span
    from isnad_start so the span never ends up unit-less.
    """
    isnad_end = span.metadata["isnad_end"]
    isnad_start = int(span.metadata.get("isnad_start", 0))
    citation_head = span.text[:isnad_start].strip()
    entry_number = _leading_entry_number(span)
    head_fields: dict[str, Any] = {}
    if citation_head:
        head_fields["citation_head"] = citation_head
    if entry_number is not None:
        head_fields["entry_number"] = entry_number
    head_metadata: dict[str, Any] | None = head_fields or None
    if isnad_end < len(span.text):
        isnad_text = strip_footnote_markers(span.text[isnad_start:isnad_end])
        matn_text = strip_footnote_markers(span.text[isnad_end:])
        if isnad_text and matn_text:
            unit_types: dict[str, Any] = config_rule["unit_types"]
            return [
                _unit(
                    span,
                    HADITH__UNIT_ID_FORMAT.format(
                        manifestation_id=manifestation_id, index=start_index
                    ),
                    isnad_text,
                    unit_types["isnad"],
                    behavior,
                    hierarchy,
                    metadata=head_metadata,
                ),
                _unit(
                    span,
                    HADITH__UNIT_ID_FORMAT.format(
                        manifestation_id=manifestation_id, index=start_index + 1
                    ),
                    matn_text,
                    unit_types["matn"],
                    behavior,
                    hierarchy,
                ),
            ]
        _logger.warning("sanad_matn_empty_split", span_id=span.span_id, isnad_end=isnad_end)

    reserve_type: str = config_rule["fallback_unit_type"]
    reserve_id = HADITH__UNIT_ID_FORMAT.format(manifestation_id=manifestation_id, index=start_index)
    return [
        _unit(
            span,
            reserve_id,
            strip_footnote_markers(span.text[isnad_start:]),
            reserve_type,
            behavior,
            hierarchy,
            metadata=head_metadata,
        )
    ]


def _unit(
    span: Span,
    unit_id: str,
    text_ar: str,
    unit_type: str,
    behavior: str,
    hierarchy: HierarchyPath,
    *,
    metadata: dict[str, Any] | None = None,
) -> Unit:
    """Build one Unit anchored on the span."""
    return Unit(
        unit_id=unit_id,
        text_ar=text_ar,
        unit_type=unit_type,
        behavior=behavior,
        span_id=span.span_id,
        page_start=span.page_start,
        page_end=span.page_end,
        hierarchy=hierarchy,
        metadata=metadata or {},
    )


def _make_footnote_unit(
    unit_id: str, footnote_text: str, behavior: str, hierarchy: HierarchyPath, span: Span
) -> Unit:
    """Build one FOOTNOTE_UNIT from a footnote entry."""
    return Unit(
        unit_id=unit_id,
        text_ar=footnote_text,
        unit_type=HADITH__UNIT_FOOTNOTE,
        behavior=behavior,
        span_id=span.span_id,
        page_start=span.page_start,
        page_end=span.page_end,
        hierarchy=hierarchy,
    )


def _resolve_isnad_back_references(manuscript: Manuscript) -> None:
    """Stamp each back-reference span's isnad-bearing unit with resolved pointers.

    A hadith opening with "بهذا الاسناد" transmits by the chain of an earlier
    hadith, so that chain is not printed on this span's page. Copying the
    source chain's text or entities here would fabricate page-anchored data
    whose offsets and pages belong to another span, so the artifact records
    pointers instead: ``refers_to_span_id`` names the hadith the wording
    points at, and ``resolved_span_id``/``resolved_unit_id`` name the nearest
    earlier span whose ISNAD unit is literal text, following chained
    back-references. Composing the effective chain from the pointer is the
    graph phase's judgment call, not this artifact's.
    """
    span_map = {span.span_id: span for span in manuscript.spans}
    for span in manuscript.spans:
        if not span.metadata.get("isnad_back_ref"):
            continue
        target = _isnad_pointer_unit(span)
        if target is None:
            _logger.warning("isnad_back_ref_span_unitless", span_id=span.span_id)
            continue
        source_span_id = span.metadata.get("refers_to_span_id")
        if source_span_id is None:
            _logger.warning("isnad_back_ref_missing_source", span_id=span.span_id)
            continue
        target.metadata["isnad_source"] = "back_reference"
        target.metadata["refers_to_span_id"] = source_span_id
        resolved = _resolve_to_literal_isnad(source_span_id, span_map)
        if resolved is None:
            _logger.warning(
                "isnad_back_ref_unresolvable",
                span_id=span.span_id,
                source_span_id=source_span_id,
            )
            continue
        resolved_span, resolved_unit = resolved
        target.metadata["resolved_span_id"] = resolved_span.span_id
        target.metadata["resolved_unit_id"] = resolved_unit.unit_id


def _isnad_pointer_unit(span: Span) -> Unit | None:
    """The unit that carries the span's back-reference pointers.

    The span's own ISNAD unit when the split produced one (the printed
    continuation, e.g. "بهذا الاسناد ، عن ابن عيسى ..."), else the whole-span
    reserve unit that holds the unsplit hadith text.
    """
    if not span.units:
        return None
    for unit in span.units:
        if unit.unit_type == HADITH__UNIT_ISNAD:
            return unit
    return span.units[0]


def _resolve_to_literal_isnad(
    source_span_id: str, span_map: dict[str, Span]
) -> tuple[Span, Unit] | None:
    """Follow chained back-references to the nearest literal ISNAD unit.

    Walks ``refers_to_span_id`` links until a span without ``isnad_back_ref``
    is reached, guarding against cycles and dangling references. Returns None
    when the walk dead-ends or the terminal span never produced an ISNAD unit;
    the caller logs, so a missing resolution is loud, never invented.
    """
    seen: set[str] = set()
    current_id: str | None = source_span_id
    while current_id is not None and current_id not in seen:
        seen.add(current_id)
        source = span_map.get(current_id)
        if source is None:
            return None
        if not source.metadata.get("isnad_back_ref"):
            for unit in source.units or []:
                if unit.unit_type == HADITH__UNIT_ISNAD:
                    return source, unit
            return None
        current_id = source.metadata.get("refers_to_span_id")
    return None
