"""Hadith narrator extractor (Phase 3).

narrator_extractor produces PERSON entities from a HADITH_TRANSMISSION span.
The chain is walked in two parts: the head narrator between the isnad start
(after any citation head; see ``extractors.isnad_boundary``) and the first
ATTRIBUTION verb, then one slice per attribution, where the text between
consecutive transmission verbs is a narrator name. Extraction caps at the
precomputed isnad_end so matn text is never read as a narrator name.

A kinship reference (عن أبيه) is a chain link but not a person name: a bare
reference emits with role ``relative_reference`` (identity resolution
deferred), and a reference followed by the actual name (عن أبيه محمد بن علي)
emits the name alone with the kinship token recorded in metadata. Genealogy
markers (بن/ابن) are part of the name and are not extracted separately.

Ported from sol-next's src/extractors/hadith.py and hadith_names.py; the
isnad boundary detection lives in ``extractors.isnad_boundary``. Name cleanup
comes from name_extraction; canonical PERSON emission from persons. Every
regex compiles through the central backend.patterns module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from backend.core.logging import get_logger
from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.extractors.isnad_boundary import (
    build_attribution_cues,
    categorize_patterns,
    filter_false_attributions,
)
from backend.pipeline.models import Entity, Pattern, Span
from backend.pipeline.name_extraction import extract_person_name
from backend.pipeline.persons import (
    NARRATOR__ROLE_NARRATOR,
    NARRATOR__ROLE_RELATIVE_REF,
    NARRATOR__SOURCE_CHAIN_WALK,
    PersonSpec,
    emit_person_entity,
)
from backend.pipeline.vocab import HADITH__PATTERN_SPEECH_VERB_GENERIC

if TYPE_CHECKING:
    from backend.pipeline.config import Config

_logger = get_logger("shia-library.pipeline.extractors.hadith")

_WORD_BOUNDARY_CHARS: frozenset[str] = frozenset(" \t\n\r،,:.؟?؛")


@dataclass(frozen=True, slots=True)
class NarratorSliceContext:
    """Shared config + span state for extracting narrators across isnad slices."""

    config: Config
    isnad_start: int
    isnad_end: int
    speech_verbs: list[Pattern]
    name_content_boundary_regex: CompiledPattern
    relative_references: list[str]
    stopwords: frozenset[str]
    narrator_name_max_chars: int


def narrator_extractor(span: Span, config: Config) -> list[Entity]:
    """Extract narrator-name entities from a hadith transmission span.

    Walks the head narrator (isnad start to first attribution) and then the
    slice after each ATTRIBUTION, capped at the precomputed isnad_end. Names
    exceeding narrator_name_max_chars are skipped rather than emitted wrong
    (wrong is worse than absent).
    """
    ctx = _build_slice_context(span, config)
    attributions = _filter_attributions(span, config, ctx.isnad_end)
    entities: list[Entity] = []
    if attributions and attributions[0].char_start > ctx.isnad_start:
        entities.extend(_narrators_in_slice(span, ctx.isnad_start, attributions[0].char_start, ctx))
    for index, attr in enumerate(attributions):
        if index + 1 < len(attributions):
            default_end = attributions[index + 1].char_start
        else:
            default_end = snap_name_end_to_word_boundary(span.text, ctx.isnad_end)
        entities.extend(_narrators_in_slice(span, attr.char_end, default_end, ctx))
    _annotate_chain_positions(entities)
    return sorted(entities, key=lambda entity: entity.char_start)


def _build_slice_context(span: Span, config: Config) -> NarratorSliceContext:
    """Assemble the per-span config + state shared across the narrator slices."""
    narrator_cfg = config.raw["narrator_extraction"]
    boundaries = narrator_cfg["name_content_boundaries"]
    boundary_parts = tuple(
        value for key, value in boundaries.items() if key != "ya_names_not_boundary"
    )
    return NarratorSliceContext(
        config=config,
        isnad_start=int(span.metadata.get("isnad_start", 0)),
        isnad_end=int(span.metadata.get("isnad_end", len(span.text))),
        speech_verbs=span.patterns_by_id(HADITH__PATTERN_SPEECH_VERB_GENERIC),
        name_content_boundary_regex=build_name_content_boundary_regex(boundary_parts),
        relative_references=list(narrator_cfg["relative_references"]),
        stopwords=frozenset(narrator_cfg.get("narrator_stopwords", [])),
        narrator_name_max_chars=config.thresholds.narrator_name_max_chars,
    )


def _filter_attributions(span: Span, config: Config, isnad_end: int) -> list[Pattern]:
    """Categorize, false-positive-filter, and isnad-cap the span's attribution verbs."""
    cues = build_attribution_cues(config)
    all_attributions, _, _ = categorize_patterns(span)
    filtered = filter_false_attributions(span, all_attributions, cues)
    return [attr for attr in filtered if attr.char_start < isnad_end]


def _narrators_in_slice(
    span: Span, name_start: int, default_end: int, ctx: NarratorSliceContext
) -> list[Entity]:
    """Extract every narrator name in span.text[name_start:default_end)."""
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


def _split_relative_reference(name: str, references: list[str]) -> tuple[str | None, str]:
    """Split a leading kinship token off a name candidate.

    Returns (reference, remainder): ('أبيه', 'محمد بن علي') for a prefixed
    name, ('أبيه', '') for a bare reference, (None, name) when the candidate
    does not open with a kinship token. Any whitespace separates the token
    from the name, a newline included: page text keeps its line breaks.
    """
    for ref in sorted(references, key=len, reverse=True):
        if name == ref:
            return ref, ""
        if name.startswith(ref) and name[len(ref) : len(ref) + 1].isspace():
            return ref, name[len(ref) :].strip()
    return None, name


def _emit_one_narrator(
    span: Span, part: str, part_search: int, ctx: NarratorSliceContext
) -> tuple[Entity | None, int]:
    """Clean, validate, and emit one narrator; return (entity or None, advanced search).

    The patronymic regex already bounded the name, so only the content-boundary
    crop and the footnote/punctuation cleanup (clean_name_text) apply. A bare
    kinship reference emits as role relative_reference; a kinship-prefixed name
    emits the name alone with the reference recorded in metadata.
    """
    cleaned = extract_person_name(part, 0, len(part), ctx.name_content_boundary_regex)
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
    advance = part_pos + len(part)
    reference, core_name = _split_relative_reference(name_text, ctx.relative_references)
    if reference is not None and not core_name:
        entity = _emit_narrator_entity(
            span, reference, char_start, ctx, role=NARRATOR__ROLE_RELATIVE_REF
        )
        return entity, advance
    if reference is not None:
        core_start = span.text.find(core_name, char_start)
        if core_start == -1:
            core_start = char_start + len(reference) + 1
        entity = _emit_narrator_entity(
            span,
            core_name,
            core_start,
            ctx,
            role=NARRATOR__ROLE_NARRATOR,
            relative_reference=reference,
        )
        return entity, advance
    entity = _emit_narrator_entity(span, name_text, char_start, ctx, role=NARRATOR__ROLE_NARRATOR)
    return entity, advance


def _emit_narrator_entity(
    span: Span,
    text: str,
    char_start: int,
    ctx: NarratorSliceContext,
    *,
    role: str,
    relative_reference: str | None = None,
) -> Entity:
    """Emit one chain-walk PERSON entity with the given role and kinship context."""
    return emit_person_entity(
        span=span,
        text=text,
        char_start=char_start,
        char_end=char_start + len(text),
        spec=PersonSpec(
            role_in_context=role,
            source=NARRATOR__SOURCE_CHAIN_WALK,
            config=ctx.config,
            extractor_id="narrator_extractor",
            is_relative_reference=role == NARRATOR__ROLE_RELATIVE_REF,
            extra_metadata=(
                {"relative_reference": relative_reference} if relative_reference else None
            ),
        ),
    )


def _annotate_chain_positions(entities: list[Entity]) -> None:
    """Stamp each chain member's position, in extraction (document) order."""
    for position, entity in enumerate(entities):
        entity.metadata["chain_position"] = position


def build_name_content_boundary_regex(boundary_patterns: tuple[str, ...]) -> CompiledPattern:
    """Compile the name/content boundary alternation from config pattern values."""
    return cached_compile(r"(?:" + "|".join(boundary_patterns) + r")")


_COMMA_WAW_SPLIT_REGEX: CompiledPattern = cached_compile(r"،\s*و")
_BARE_WAW_REGEX: CompiledPattern = cached_compile(r"\s+و")
_IBN_BEFORE_WAW_REGEX: CompiledPattern = cached_compile(r"(?:بن|ابن)\s*$")


def split_co_narrators(name_slice: str, relative_references: list[str]) -> list[str]:
    """Split a name slice containing co-narrators joined by conjunction.

    Comma-waw (، و) always splits — unambiguous Arabic co-narrator syntax. Bare
    waw (و) splits with guards: not when preceded by بن/ابن (بن وهب is a name),
    not when followed by a relative reference (وأبيه) or an identity
    clarification (هو/هي). Returns [name_slice] when no split applies.
    """
    parts = _COMMA_WAW_SPLIT_REGEX.split(name_slice)
    if len(parts) > 1:
        return [part.strip() for part in parts if part.strip()]

    result: list[str] = []
    remaining = name_slice
    while remaining:
        match = _BARE_WAW_REGEX.search(remaining)
        if match is None:
            result.append(remaining)
            break
        before = remaining[: match.start()]
        after = remaining[match.end() :]
        if not _bare_waw_splits(before, after, relative_references):
            result.append(remaining)
            break
        if before.strip():
            result.append(before)
        remaining = after
    return [part.strip() for part in result if part.strip()] or [name_slice]


def _bare_waw_splits(before: str, after: str, relative_references: list[str]) -> bool:
    """Return True when a bare و at this position is a co-narrator conjunction.

    Guards against splitting a name-internal و: the و is not a conjunction when it
    follows بن/ابن (بن وهب), opens a relative reference (وأبيه), or opens an
    identity clarification (وهو/هي).
    """
    if _IBN_BEFORE_WAW_REGEX.search(before):
        return False
    after_stripped = after.lstrip()
    if any(after_stripped.startswith(ref) for ref in relative_references):
        return False
    return not after_stripped.startswith(("هو", "هي"))


def snap_name_end_to_word_boundary(text: str, pos: int) -> int:
    """Extend pos to the end of the current word when it falls mid-word.

    When isnad_end lands mid-name (truncating عقيل to ع), extend to the next
    whitespace/punctuation boundary so the full name is captured. When pos is
    already at a boundary (preceded by such a char) or at/past the text end, it is
    returned unchanged.
    """
    if pos <= 0 or pos >= len(text):
        return pos
    if text[pos - 1] in _WORD_BOUNDARY_CHARS:
        return pos
    while pos < len(text) and text[pos] not in _WORD_BOUNDARY_CHARS:
        pos += 1
    return pos
