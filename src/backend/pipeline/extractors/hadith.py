"""Hadith narrator extractor (Phase 3).

narrator_extractor produces PERSON entities from a HADITH_TRANSMISSION span by
treating ATTRIBUTION pattern positions as delimiters: the text between consecutive
transmission verbs is a narrator name. The isnad boundary (find_isnad_end, stored
on span.metadata) caps extraction so matn text is never read as a narrator name;
its cascading priority chain of boundary signals (speech-verb cap,
MATN_BOUNDARY_HINT, chain-gap break, أنه-clause) lives here too, as do the
co-narrator splitting and name-end snapping helpers. Genealogy markers (بن/ابن)
are part of the name and are not extracted separately.

Ported from sol-next's src/extractors/hadith.py and hadith_names.py; the isnad
boundary detection and the name helpers were once shards under the old file-size
cap and now live with the extractor. Name cleanup comes from name_extraction;
canonical PERSON emission from persons. Every regex compiles through the central
backend.patterns module; attribution-cue fields use the _regex suffix so method
calls don't read as bare re.match/re.search to the grep checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from backend.core.constants import (
    HADITH__PATTERN_ATTRIBUTION,
    HADITH__PATTERN_MATN_BOUNDARY_HINT,
    HADITH__PATTERN_SPEECH_VERB_GENERIC,
)
from backend.core.logging import get_logger
from backend.patterns import (
    CompiledPattern,
    cached_compile,
    cached_compile_alternation,
    escape_pattern,
)
from backend.pipeline.models import Entity, Pattern, Span
from backend.pipeline.name_extraction import extract_person_name
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
        narrator_name_max_chars=config.thresholds.narrator_name_max_chars,
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

    The patronymic regex already bounded the name, so only the content-boundary
    crop and the footnote/punctuation cleanup (clean_name_text) apply.
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


_QUESTION_VERB_REGEX: CompiledPattern = cached_compile(r"(?:سألت[هاهمي]*|سئل[ت]*|يسأل)")
_AN_CLAUSE_REGEX: CompiledPattern = cached_compile(r"أنه[ام]?\s")
_QALA_BEFORE_ANA_REGEX: CompiledPattern = cached_compile(r"قال[ته]?\s*:?\s*$")
_MIN_CHAIN_ATTRIBUTIONS: int = 2


@dataclass(frozen=True, slots=True)
class AttributionCues:
    """Compiled patterns + thresholds for attribution false-positive filtering.

    disqualifier_lookahead is the post-verb char window for the prepositional عن and
    pronoun أنا disqualifiers; narrative_lookahead is the tighter window for the
    narrative سمعت check. sol-next uses 20 and 15 respectively, and both windows are
    read from config so the per-check widths match sol-next exactly.
    """

    question_verb_lookback: int
    prepositional_regex: CompiledPattern
    narrative_regex: CompiledPattern
    disqualifier_lookahead: int
    narrative_lookahead: int
    ana_pronoun_regex: CompiledPattern | None = None


def build_attribution_cues(config: Config) -> AttributionCues:
    """Compile the attribution false-positive filter cues from config."""
    narrator_cfg = config.raw["narrator_extraction"]
    ana_exclusions = narrator_cfg.get("pronoun_ana_exclusions")
    return AttributionCues(
        question_verb_lookback=config.thresholds.question_verb_lookback_chars,
        prepositional_regex=_build_exclusion_regex(
            tuple(narrator_cfg["prepositional_an_exclusions"])
        ),
        narrative_regex=_build_exclusion_regex(tuple(narrator_cfg["narrative_context_words"])),
        disqualifier_lookahead=config.thresholds.narrator_disqualifier_lookahead_chars,
        narrative_lookahead=config.thresholds.narrator_narrative_lookahead_chars,
        ana_pronoun_regex=_build_exclusion_regex(tuple(ana_exclusions)) if ana_exclusions else None,
    )


def _build_exclusion_regex(words: tuple[str, ...]) -> CompiledPattern:
    """Compile a config word list into an anchored exclusion alternation."""
    return cached_compile_alternation(
        tuple(escape_pattern(word) for word in words),
        prefix=r"^\s*(?:",
        suffix=r")",
    )


def build_name_content_boundary_regex(boundary_patterns: tuple[str, ...]) -> CompiledPattern:
    """Compile the name/content boundary alternation from config pattern values."""
    return cached_compile(r"(?:" + "|".join(boundary_patterns) + r")")


def categorize_patterns(
    span: Span,
) -> tuple[list[Pattern], list[Pattern], list[Pattern]]:
    """Split a span's patterns into attributions, matn hints, and speech verbs."""
    attributions: list[Pattern] = []
    matn_hints: list[Pattern] = []
    speech_verbs: list[Pattern] = []
    for pattern in span.patterns:
        if pattern.pattern_id == HADITH__PATTERN_ATTRIBUTION:
            attributions.append(pattern)
        elif pattern.pattern_id == HADITH__PATTERN_MATN_BOUNDARY_HINT:
            matn_hints.append(pattern)
        elif pattern.pattern_id == HADITH__PATTERN_SPEECH_VERB_GENERIC:
            speech_verbs.append(pattern)
    attributions.sort(key=lambda p: p.char_start)
    matn_hints.sort(key=lambda p: p.char_start)
    speech_verbs.sort(key=lambda p: p.char_start)
    return attributions, matn_hints, speech_verbs


def _disqualifies_as_prepositional_about(span: Span, attr: Pattern, cues: AttributionCues) -> bool:
    """عن after a question verb, or عن before a spatial/directional word."""
    if attr.matched_text.strip() not in ("عن", "وعن"):
        return False
    lookback = span.text[max(0, attr.char_start - cues.question_verb_lookback) : attr.char_start]
    if _QUESTION_VERB_REGEX.search(lookback):
        return True
    after = span.text[attr.char_end : attr.char_end + cues.disqualifier_lookahead]
    return bool(cues.prepositional_regex.match(after))


def _disqualifies_as_narrative(span: Span, attr: Pattern, cues: AttributionCues) -> bool:
    """سمعت/سمعنا followed by a narrative-context word (في/ذلك/هذا/شيئ)."""
    if attr.matched_text.strip() not in ("سمعت", "سمعنا"):
        return False
    after = span.text[attr.char_end : attr.char_end + cues.narrative_lookahead]
    return bool(cues.narrative_regex.match(after))


def _disqualifies_as_pronoun_ana(span: Span, attr: Pattern, cues: AttributionCues) -> bool:
    """أنا as the pronoun "I": after قال/قالت, or followed by a first-person word."""
    if attr.matched_text.strip() not in ("أنا", "وأنا"):
        return False
    lookback = span.text[max(0, attr.char_start - cues.question_verb_lookback) : attr.char_start]
    if _QALA_BEFORE_ANA_REGEX.search(lookback):
        return True
    if cues.ana_pronoun_regex is None:
        return False
    after = span.text[attr.char_end : attr.char_end + cues.disqualifier_lookahead]
    return bool(cues.ana_pronoun_regex.match(after))


def filter_false_attributions(
    span: Span, attributions: list[Pattern], cues: AttributionCues
) -> list[Pattern]:
    """Drop attributions that are prepositional, narrative, or pronominal."""
    filtered: list[Pattern] = []
    for attr in attributions:
        if _disqualifies_as_prepositional_about(span, attr, cues):
            continue
        if _disqualifies_as_narrative(span, attr, cues):
            continue
        if _disqualifies_as_pronoun_ana(span, attr, cues):
            continue
        filtered.append(attr)
    return filtered


def _find_chain_end(span: Span, attributions: list[Pattern], isnad_chain_gap_max: int) -> int:
    """Find where the consecutive-attribution chain structure breaks.

    In a valid isnad (عن X ، عن Y ، عن Z) the gap between consecutive attribution
    verbs is a narrator name. When a gap exceeds isnad_chain_gap_max the chain has
    broken and the rest is matn. Returns the break point plus the gap threshold
    (to include the last name), or len(span.text) if the chain never breaks.
    """
    if len(attributions) < _MIN_CHAIN_ATTRIBUTIONS:
        return len(span.text)
    for index in range(len(attributions) - 1):
        gap = attributions[index + 1].char_start - attributions[index].char_end
        if gap > isnad_chain_gap_max:
            return min(attributions[index].char_end + isnad_chain_gap_max, len(span.text))
    last_attr = attributions[-1]
    remaining = len(span.text) - last_attr.char_end
    if remaining > isnad_chain_gap_max:
        return min(last_attr.char_end + isnad_chain_gap_max, len(span.text))
    return len(span.text)


def _find_an_clause_boundary(span: Span, attributions: list[Pattern]) -> int:
    """Find an أنه/أنها clause boundary after the last attribution, else text end."""
    if not attributions:
        return len(span.text)
    last_attr_end = attributions[-1].char_end
    match = _AN_CLAUSE_REGEX.search(span.text[last_attr_end:])
    if match is None:
        return len(span.text)
    return last_attr_end + match.start()


def _speech_verb_cap_from(
    span: Span,
    isnad_chain_proximity_max: int,
    attributions: list[Pattern],
    speech_verbs: list[Pattern],
) -> int:
    """Return the first terminal speech verb, or len(span.text).

    A speech verb is terminal (ends the isnad) when no ATTRIBUTION follows within
    isnad_chain_proximity_max chars — this distinguishes intermediate قال (immediately
    followed by the next attribution) from the final verb that introduces the matn.
    """
    if not attributions:
        return len(span.text)
    attr_starts = {attr.char_start for attr in attributions}
    first_attr_end = attributions[0].char_end
    for verb in speech_verbs:
        if verb.char_start < first_attr_end:
            continue
        has_nearby = any(
            verb.char_end <= start <= verb.char_end + isnad_chain_proximity_max
            for start in attr_starts
        )
        if not has_nearby:
            return verb.char_start
    return len(span.text)


def find_isnad_end(
    span: Span,
    isnad_chain_proximity_max: int,
    isnad_chain_gap_max: int,
    cues: AttributionCues,
) -> int:
    """Determine the character position where the isnad ends and matn begins.

    Cascading priority: filter false-positive attributions, then speech-verb cap,
    then a MATN_BOUNDARY_HINT inside the isnad zone, then the speech cap itself,
    then chain-gap break, then an أنه/أنها clause, finally len(span.text) when no
    boundary is found.
    """
    all_attributions, all_matn_hints, speech_verbs = categorize_patterns(span)
    attributions = filter_false_attributions(span, all_attributions, cues)
    if not attributions:
        return len(span.text)

    speech_cap = _speech_verb_cap_from(span, isnad_chain_proximity_max, attributions, speech_verbs)
    isnad_attrs = [attr for attr in attributions if attr.char_start < speech_cap]
    last_attr_start = isnad_attrs[-1].char_start if isnad_attrs else 0
    matn_hints = [
        pattern for pattern in all_matn_hints if last_attr_start <= pattern.char_start <= speech_cap
    ]
    if matn_hints:
        return matn_hints[0].char_start
    if speech_cap < len(span.text):
        return speech_cap
    chain_end = _find_chain_end(span, attributions, isnad_chain_gap_max)
    if chain_end < len(span.text):
        return chain_end
    an_boundary = _find_an_clause_boundary(span, attributions)
    if an_boundary < len(span.text):
        return an_boundary
    return len(span.text)


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
