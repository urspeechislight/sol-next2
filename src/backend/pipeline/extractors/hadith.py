"""Hadith narrator extractor (Phase 3).

narrator_extractor produces PERSON entities from a HADITH_TRANSMISSION span by
treating ATTRIBUTION pattern positions as delimiters: the text between consecutive
transmission verbs is a narrator name. The isnad boundary (computed by
find_isnad_end in _hadith_isnad and stored on span.metadata) caps extraction so
matn text is never read as a narrator name. Genealogy markers (بن/ابن) are part of
the name and are not extracted separately.

Ported from sol-next's src/extractors/hadith.py (the extraction half), decomposed
under the function-size cap. Co-narrator splitting and the name-end snap come from
hadith_names; name cleanup from name_extraction; canonical PERSON emission from
persons.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from backend.core.constants import HADITH__PATTERN_SPEECH_VERB_GENERIC
from backend.core.logging import get_logger
from backend.patterns import CompiledPattern
from backend.pipeline.extractors._hadith_isnad import (
    build_attribution_cues,
    build_name_content_boundary_regex,
    categorize_patterns,
    filter_false_attributions,
)
from backend.pipeline.hadith_names import snap_name_end_to_word_boundary, split_co_narrators
from backend.pipeline.models import Entity, Pattern, Span
from backend.pipeline.name_extraction import NameOptions, extract_person_name
from backend.pipeline.persons import (
    NARRATOR__ROLE_NARRATOR,
    NARRATOR__SOURCE_CHAIN_WALK,
    PersonSpec,
    emit_person_entity,
)

if TYPE_CHECKING:
    from backend.pipeline.config import Config

_logger = get_logger("shia-library.pipeline.extractors.hadith")

_WORD_BOUNDARY_CHARS: frozenset[str] = frozenset(" \t\n\r،,:.؟?؛")


@dataclass(frozen=True, slots=True)
class NarratorSliceContext:
    """Shared config + span state for extracting narrators across isnad slices."""

    config: Config
    isnad_end: int
    speech_verbs: list[Pattern]
    name_content_boundary_regex: CompiledPattern
    relative_references: list[str]
    stopwords: frozenset[str]
    narrator_name_max_chars: int


def get_narrator_entities(span: Span) -> list[Entity]:
    """Return PERSON entities with role_in_context narrator from a span."""
    return span.persons_by_role(NARRATOR__ROLE_NARRATOR)


def narrator_extractor(span: Span, config: Config) -> list[Entity]:
    """Extract narrator-name entities from a hadith transmission span.

    Uses ATTRIBUTION positions to slice narrator names from the isnad, capped at
    the precomputed isnad_end. Names exceeding narrator_name_max_chars are skipped
    rather than emitted wrong (wrong is worse than absent).
    """
    ctx = _build_slice_context(span, config)
    attributions = _filter_attributions(span, config, ctx.isnad_end)
    entities: list[Entity] = []
    for index, attr in enumerate(attributions):
        if index + 1 < len(attributions):
            default_end = attributions[index + 1].char_start
        else:
            default_end = snap_name_end_to_word_boundary(span.text, ctx.isnad_end)
        entities.extend(_narrators_for_attribution(span, attr, default_end, ctx))
    _annotate_chain_positions(entities, ctx.relative_references)
    return _validate_narrator_names(entities)


def _build_slice_context(span: Span, config: Config) -> NarratorSliceContext:
    """Assemble the per-span config + state shared across the attribution slices."""
    narrator_cfg = config.raw["narrator_extraction"]
    boundaries = narrator_cfg["name_content_boundaries"]
    boundary_parts = tuple(
        value for key, value in boundaries.items() if key != "ya_names_not_boundary"
    )
    return NarratorSliceContext(
        config=config,
        isnad_end=span.metadata.get("isnad_end", len(span.text)),
        speech_verbs=span.patterns_by_id(HADITH__PATTERN_SPEECH_VERB_GENERIC),
        name_content_boundary_regex=build_name_content_boundary_regex(boundary_parts),
        relative_references=list(narrator_cfg["relative_references"]),
        stopwords=frozenset(narrator_cfg.get("narrator_stopwords", [])),
        narrator_name_max_chars=config.threshold_int("narrator_name_max_chars"),
    )


def _filter_attributions(span: Span, config: Config, isnad_end: int) -> list[Pattern]:
    """Categorize, false-positive-filter, and isnad-cap the span's attribution verbs."""
    cues = build_attribution_cues(config)
    all_attributions, _, _ = categorize_patterns(span)
    filtered = filter_false_attributions(span, all_attributions, cues)
    return [attr for attr in filtered if attr.char_start < isnad_end]


def _narrators_for_attribution(
    span: Span, attr: Pattern, default_end: int, ctx: NarratorSliceContext
) -> list[Entity]:
    """Extract every narrator name between one attribution and the next boundary."""
    name_start = attr.char_end
    name_end = _resolve_name_end(span, name_start, default_end, ctx)
    name_slice = span.text[name_start:name_end]
    content_match = ctx.name_content_boundary_regex.search(name_slice)
    if content_match is not None:
        name_slice = name_slice[: content_match.start()]
    entities: list[Entity] = []
    part_search = name_start
    for part in split_co_narrators(name_slice, ctx.relative_references):
        entity, part_search = _emit_one_narrator(span, part, part_search, ctx)
        if entity is not None:
            entities.append(entity)
    return entities


def _resolve_name_end(
    span: Span, name_start: int, default_end: int, ctx: NarratorSliceContext
) -> int:
    """Cap the name at the first speech verb in the slice, else the snapped default."""
    name_end = snap_name_end_to_word_boundary(span.text, default_end)
    for verb in ctx.speech_verbs:
        in_slice = name_start < verb.char_start < name_end
        precedes_boundary = (
            verb.char_start == 0 or span.text[verb.char_start - 1] in _WORD_BOUNDARY_CHARS
        )
        if in_slice and precedes_boundary:
            return verb.char_start
    return name_end


def _emit_one_narrator(
    span: Span, part: str, part_search: int, ctx: NarratorSliceContext
) -> tuple[Entity | None, int]:
    """Clean, validate, and emit one narrator; return (entity or None, advanced search).

    The clitic/compound/dangling cleanup is disabled here — the patronymic regex
    already bounded the name, so only footnote/punctuation cleanup (clean_name_text)
    and the content-boundary crop apply.
    """
    cleaned = extract_person_name(
        part,
        0,
        len(part),
        NameOptions(
            boundary_regex=ctx.name_content_boundary_regex,
            clitic_min_word_chars=0,
            extend_compound_prefix=False,
            strip_clitic=False,
            strip_dangling_connector=False,
        ),
    )
    if cleaned is None:
        return None, part_search
    name_text, part_lo, part_hi = cleaned
    part = part[part_lo:part_hi]
    if not name_text or name_text in ctx.stopwords:
        return None, part_search
    if len(name_text) > ctx.narrator_name_max_chars:
        _logger.debug(
            "narrator_name_oversize_skipped",
            span_id=span.span_id,
            name_chars=len(name_text),
        )
        return None, part_search
    part_pos = span.text.find(part, part_search)
    if part_pos == -1:
        part_pos = part_search
    leading = len(part) - len(part.lstrip())
    char_start = part_pos + leading
    entity = emit_person_entity(
        span=span,
        text=name_text,
        char_start=char_start,
        char_end=char_start + len(name_text),
        spec=PersonSpec(
            role_in_context=NARRATOR__ROLE_NARRATOR,
            source=NARRATOR__SOURCE_CHAIN_WALK,
            config=ctx.config,
            extractor_id="narrator_extractor",
        ),
    )
    return entity, part_pos + len(part)


def _annotate_chain_positions(entities: list[Entity], relative_references: list[str]) -> None:
    """Stamp each entity's chain position and flag relative-reference names."""
    for position, entity in enumerate(entities):
        entity.metadata["chain_position"] = position
        if any(ref in entity.text for ref in relative_references):
            entity.metadata["is_relative_reference"] = True


def _validate_narrator_names(entities: list[Entity]) -> list[Entity]:
    """Pass extracted narrators through in span order; external checks deferred.

    The narrator gazetteer is empty and the NER service is disabled in this port,
    so no external signal can veto a candidate — every extracted narrator is kept.
    The three-tier gazetteer-then-NER filter is restored when those services land.
    """
    return sorted(entities, key=lambda entity: entity.char_start)
