"""Isnad boundary detection: where a transmission chain starts and ends.

Owns the attribution-cue compilation, the false-positive filters, and
``find_isnad_bounds``: the one place the isnad's [start, end) character
window inside a HADITH_TRANSMISSION span is decided. The start skips the
citation head Majlisi-style compilations print before the chain (the hadith
ordinal and the source works, ``2 - التوحيد ، عيون أخبار الرضا :``): that
head is bibliography, not transmission, so it must never reach the ISNAD
unit or the narrator walk. The end is a cascading priority chain of boundary
signals (speech-verb cap, MATN_BOUNDARY_HINT, chain-gap break, أنه-clause).

Split out of ``extractors/hadith.py``, which keeps the narrator walk itself;
extract.py stores both bounds on span.metadata for the atomicizer and the
extractor to share.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.patterns import (
    CompiledPattern,
    cached_compile,
    cached_compile_alternation,
    escape_pattern,
)
from backend.pipeline.config import Config
from backend.pipeline.models import Pattern, Span
from backend.pipeline.vocab import (
    HADITH__PATTERN_ATTRIBUTION,
    HADITH__PATTERN_MATN_BOUNDARY_HINT,
    HADITH__PATTERN_NUMBERED_ENTRY,
    HADITH__PATTERN_SPEECH_VERB_GENERIC,
)

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


def _find_isnad_start(span: Span, attributions: list[Pattern]) -> int:
    """Skip the citation head: the chain starts after the last colon that
    precedes the first attribution verb, and never before the end of a
    leading numbered-entry marker.

    Majlisi-style compilations open each hadith with an ordinal and its source
    works, closed by a colon (``2 - التوحيد ، عيون أخبار الرضا :``); the
    narrators start after it. A numbered hadith with no source citation
    (al-Kafi style, ``2 - علي بن إبراهيم ، عن أبيه``) still opens with the
    ordinal marker, so the marker's end bounds the start even without a
    colon. A chain with neither starts at 0.
    """
    head = span.text[: attributions[0].char_start]
    start = 0
    colon = head.rfind(":")
    if colon != -1:
        start = colon + 1
    for marker in span.patterns_by_id(HADITH__PATTERN_NUMBERED_ENTRY):
        opens_span = not span.text[: marker.char_start].strip()
        if opens_span and marker.char_end > start:
            start = marker.char_end
            break
    while start < len(span.text) and span.text[start].isspace():
        start += 1
    return start


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


def find_isnad_bounds(
    span: Span,
    isnad_chain_proximity_max: int,
    isnad_chain_gap_max: int,
    cues: AttributionCues,
) -> tuple[int, int]:
    """Determine the [start, end) character window of the isnad within the span.

    Start skips the citation head (see _find_isnad_start). End cascades:
    filter false-positive attributions, then speech-verb cap, then a
    MATN_BOUNDARY_HINT inside the isnad zone, then the speech cap itself, then
    chain-gap break, then an أنه/أنها clause, finally len(span.text) when no
    boundary is found. A span with no true attributions has no chain:
    (0, len(span.text)).
    """
    all_attributions, all_matn_hints, speech_verbs = categorize_patterns(span)
    attributions = filter_false_attributions(span, all_attributions, cues)
    if not attributions:
        return 0, len(span.text)
    start = _find_isnad_start(span, attributions)

    speech_cap = _speech_verb_cap_from(span, isnad_chain_proximity_max, attributions, speech_verbs)
    isnad_attrs = [attr for attr in attributions if attr.char_start < speech_cap]
    last_attr_start = isnad_attrs[-1].char_start if isnad_attrs else 0
    matn_hints = [
        pattern for pattern in all_matn_hints if last_attr_start <= pattern.char_start <= speech_cap
    ]
    if matn_hints:
        return start, max(start, matn_hints[0].char_start)
    if speech_cap < len(span.text):
        return start, max(start, speech_cap)
    chain_end = _find_chain_end(span, attributions, isnad_chain_gap_max)
    if chain_end < len(span.text):
        return start, max(start, chain_end)
    an_boundary = _find_an_clause_boundary(span, attributions)
    if an_boundary < len(span.text):
        return start, max(start, an_boundary)
    return start, len(span.text)
