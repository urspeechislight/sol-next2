"""Phase 3: EXTRACT.

Input: a Manuscript whose spans carry behavior + hierarchy from Phase 2.
Output: the same Manuscript with each span's entities and units populated.

For each span, gated by span.behavior: (1) run the registered extractors to
produce Entity objects from the already-detected patterns, assigning entity ids
scoped to the span; (2) atomicize the span into Unit objects via the configured
strategy. A HADITH_TRANSMISSION span also gets its isnad_end computed here so the
sanad/matn split and narrator extraction cap at the matn boundary. A content span
that produces zero units is a bug and raises ExtractError.

Ported from sol-next's src/phases/extract.py, decomposed across _extract_atomicize
(atomicizer strategies) and _extract_backrefs (isnad back-references) to stay
under the file and function caps.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.core.constants import (
    HADITH__ENTITY_ID_FORMAT,
    HADITH__PATTERN_ATTRIBUTION,
    HADITH__STRATEGY_SANAD_MATN,
    HADITH__UNIT_ID_FORMAT,
)
from backend.core.errors import ExtractError
from backend.core.logging import get_logger
from backend.pipeline._extract_atomicize import AtomizeArgs, atomicize_span, make_footnote_unit
from backend.pipeline._extract_backrefs import handle_isnad_back_references
from backend.pipeline.config import Config
from backend.pipeline.contracts import PHASE_CONTRACTS, validate_manuscript_for_phase
from backend.pipeline.extractors import EXTRACTOR_REGISTRY, VALID_ENTITY_TYPES, ExtractorFn
from backend.pipeline.extractors._hadith_isnad import (
    AttributionCues,
    build_attribution_cues,
    find_isnad_end,
)
from backend.pipeline.models import DegradedMode, Entity, Manuscript, Span, ValidationIssue
from backend.pipeline.ner import is_circuit_open
from backend.pipeline.text import split_footnote_entries

_logger = get_logger("shia-library.pipeline.extract")
_DEGRADED_SEVERITY_WARNING = "warning"
_DEGRADED_SEVERITY_INFO = "info"


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
    unit_counter = handle_isnad_back_references(manuscript, unit_counter, config)
    _record_ner_state(run)
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
        span.metadata["isnad_end"] = find_isnad_end(
            span,
            run.config.thresholds.isnad_chain_proximity_max,
            run.config.thresholds.isnad_chain_gap_max,
            run.cues,
        )
    entities = _extract_entities(span, run.registry, behavior, run.config)
    for idx, entity in enumerate(entities):
        _validate_entity_type(entity)
        _assign_entity_id(entity, span.span_id, idx)
    units = atomicize_span(
        span,
        unit_counter,
        AtomizeArgs(config_rule, run.manuscript.manifestation_id, behavior, hierarchy),
        strategy,
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
                make_footnote_unit(
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


def _record_ner_state(run: _ExtractRun) -> None:
    """Flag the NER-unavailable degraded mode when the NER circuit breaker is open."""
    if not run.config.services.get("ner", {}).get("enabled"):
        return
    if not is_circuit_open():
        return
    run.manuscript.degraded_modes.add(DegradedMode.NER_UNAVAILABLE)
    run.manuscript.validation_issues.append(
        _degraded_issue(
            DegradedMode.NER_UNAVAILABLE,
            None,
            "NER circuit breaker tripped; name validation weakened",
            _DEGRADED_SEVERITY_WARNING,
        )
    )


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
