"""Isnad-continuation boundary merging for the segment phase.

After the boundary splitter splits text into paragraphs, some splits are
false: an attribution verb that continues an isnad chain from the previous
line (e.g. "قال : حدثني جابر", where the حدثني is the next chain link, not a
new hadith). This module owns the whole repair: the config-driven regex
builders, the ``MergeCues`` bundle built once at startup, and the merge walk
itself. Ported from sol-next's src/utils/boundaries.py; previously split
into a facade plus two shards for the old file-size cap, now one module.

``build_merge_cues`` returns ``None`` when merging cannot apply (no
attribution regex for the genre, no narrator_extraction section, or no
SPEECH_VERB_GENERIC pattern); the word-list regexes are only ever produced
together, so a partial cue set cannot exist and ``MergeCues`` carries
required fields. Every regex compiles through backend.patterns
(CENTRAL-002); callers never import re. Compiled-pattern names are
lowercase/_regex-suffixed so method calls do not collide with a crude
``re.search`` substring grep in the legacy hook.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from backend.patterns import (
    CompiledPattern,
    cached_compile,
    cached_compile_alternation,
    escape_pattern,
)

if TYPE_CHECKING:
    from backend.pipeline.config import Thresholds

patronymic_tail: CompiledPattern = cached_compile(r"(?:بن|ابن|بنت)\s+\S+(?:\s+\S+){0,2}[\s،,]*$")
kunya_tail: CompiledPattern = cached_compile(r"(?:أبو|أبي|أبا)\s+\S+(?:\s+\S+)?[\s،,]*$")
trailing_comma: CompiledPattern = cached_compile(r"[،,]\s*$")
sentence_end: CompiledPattern = cached_compile(r'[.؟؟»"\]\)]\s*$')
footnote_tail: CompiledPattern = cached_compile(r"\s*\(\d+\)\s*$")


def build_chain_continuation_re(prepositional_exclusions: Sequence[str]) -> CompiledPattern:
    """Regex matching عن/وعن + name at text start, excluding prepositional uses."""
    parts = tuple(escape_pattern(w) for w in prepositional_exclusions)
    return cached_compile_alternation(parts, prefix=r"^\s*(?:و?عن)\s+(?!", suffix=r")")


def build_narrative_samitu_re(narrative_context_words: Sequence[str]) -> CompiledPattern:
    """Regex matching narrative سمعت/سمعنا + context words (false boundaries)."""
    parts = tuple(escape_pattern(w) for w in narrative_context_words)
    return cached_compile_alternation(parts, prefix=r"^\s*(?:سمعت|سمعنا)\s+(?:", suffix=r")")


def build_transmission_tail_re(verbs: Sequence[str]) -> CompiledPattern:
    """Regex matching present-tense transmission verbs at end of text."""
    parts = tuple(escape_pattern(v) for v in verbs)
    return cached_compile_alternation(parts, prefix=r"(?:", suffix=r")\s*$")


def _build_speech_verb_res(speech_verb_regex: str) -> tuple[CompiledPattern, CompiledPattern]:
    """Build isnad-continuation + speech-verb-tail regexes from SPEECH_VERB_GENERIC."""
    isnad_continuation_regex = cached_compile(rf"(?:{speech_verb_regex})\s*:\s*$")
    speech_verb_tail_regex = cached_compile(rf"(?:{speech_verb_regex})\s*$")
    return isnad_continuation_regex, speech_verb_tail_regex


@dataclass(frozen=True, slots=True)
class MergeCues:
    """The complete cue set for isnad-continuation merging.

    Built once at startup by ``build_merge_cues``. The four word-list regexes
    are required because config produces them together; only the strong
    attribution regex and the transmission tail are genuinely optional.
    """

    attribution_regex: CompiledPattern
    isnad_tail_max_chars: int
    chain_continuation_regex: CompiledPattern
    narrative_samitu_regex: CompiledPattern
    isnad_continuation_regex: CompiledPattern
    speech_verb_tail_regex: CompiledPattern
    attribution_strong_regex: CompiledPattern | None
    merge_name_max_chars: int
    transmission_tail_regex: CompiledPattern | None


def build_merge_cues(
    config_raw: dict[str, Any],
    patterns: list[dict[str, Any]],
    attribution_regex: CompiledPattern | None,
    attribution_strong_regex: CompiledPattern | None,
    thresholds: Thresholds,
) -> MergeCues | None:
    """Build the merge cue set from config, or None when merging cannot apply.

    None means: the genre has no attribution regex, the narrator_extraction
    section is absent, or the SPEECH_VERB_GENERIC pattern is missing. In each
    case there is nothing the merge walk could do, so the caller skips it.
    """
    if attribution_regex is None:
        return None
    ncfg = config_raw.get("narrator_extraction")
    if ncfg is None:
        return None
    speech_verb_entry = next((p for p in patterns if p["id"] == "SPEECH_VERB_GENERIC"), None)
    if speech_verb_entry is None:
        return None
    tail_verbs = ncfg.get("transmission_tail_verbs", [])
    isnad_cont_regex, speech_tail_regex = _build_speech_verb_res(speech_verb_entry["regex"])
    return MergeCues(
        attribution_regex=attribution_regex,
        isnad_tail_max_chars=thresholds.isnad_tail_max_chars,
        chain_continuation_regex=build_chain_continuation_re(ncfg["prepositional_an_exclusions"]),
        narrative_samitu_regex=build_narrative_samitu_re(ncfg["narrative_context_words"]),
        isnad_continuation_regex=isnad_cont_regex,
        speech_verb_tail_regex=speech_tail_regex,
        attribution_strong_regex=attribution_strong_regex,
        merge_name_max_chars=thresholds.isnad_merge_name_max_chars,
        transmission_tail_regex=build_transmission_tail_re(tail_verbs) if tail_verbs else None,
    )


def merge_isnad_continuations(
    paragraphs: list[tuple[str, int, int]],
    cues: MergeCues | None,
) -> list[tuple[str, int, int]]:
    """Merge consecutive paragraphs where an attribution verb continues an isnad chain.

    ``cues`` is None when merging cannot apply (see ``build_merge_cues``);
    the paragraphs pass through untouched.
    """
    if cues is None:
        return paragraphs
    merged: list[tuple[str, int, int]] = []
    i = 0
    while i < len(paragraphs):
        text, pg_start, pg_end = paragraphs[i]
        while i + 1 < len(paragraphs) and _should_merge_next(text, paragraphs[i + 1][0], cues):
            next_text, _, next_pg_end = paragraphs[i + 1]
            text = text + "\n" + next_text
            pg_end = next_pg_end
            i += 1
        merged.append((text, pg_start, pg_end))
        i += 1
    return merged


def _should_merge_next(text: str, next_text: str, cues: MergeCues) -> bool:
    """Return True when the next paragraph should be merged into the current one.

    Five trigger shapes (any one sufficient): speech-verb + attribution
    continuation; isnad tail + عن chain continuation; narrative سمعت false
    boundary; a merge tail (trailing comma, speech-verb tail, or transmission-verb
    tail) + chain continuation; and speech-verb tail + ATTRIBUTION_STRONG
    (guarded by ATTRIBUTION_STRONG also in current text).
    """
    next_stripped = next_text.lstrip()
    if cues.isnad_continuation_regex.search(text) and cues.attribution_regex.match(next_stripped):
        return True
    if _has_isnad_tail(
        text,
        cues.isnad_tail_max_chars,
        cues.attribution_regex,
        cues.attribution_strong_regex,
        cues.merge_name_max_chars,
    ) and cues.chain_continuation_regex.match(next_stripped):
        return True
    if cues.narrative_samitu_regex.match(next_stripped):
        return True
    if cues.chain_continuation_regex.match(next_stripped) and _text_ends_with_merge_tail(
        text, cues
    ):
        return True
    return _is_speech_verb_to_attr_strong(
        text, next_stripped, cues.speech_verb_tail_regex, cues.attribution_strong_regex
    )


def _has_isnad_tail(
    text: str,
    isnad_tail_max_chars: int,
    attribution_regex: CompiledPattern,
    attribution_strong_regex: CompiledPattern | None = None,
    merge_name_max_chars: int = 0,
) -> bool:
    """Return True when text ends with an isnad tail.

    An isnad tail is a patronymic ending (بن/ابن/بنت + name words), a kunya
    ending (أبو/أبي/أبا + name), a trailing attribution verb at the very end,
    or a short narrator name after a strong/broad attribution verb without a
    sentence-ending marker.
    """
    tail = text[-isnad_tail_max_chars:] if len(text) > isnad_tail_max_chars else text
    tail = footnote_tail.sub("", tail)
    if patronymic_tail.search(tail):
        return True
    if kunya_tail.search(tail):
        return True
    attr_match = attribution_regex.search(tail)
    if attr_match and attr_match.end() >= len(tail.rstrip()):
        return True
    if attribution_strong_regex is not None and _ends_with_strong_attr_name(
        tail, attribution_strong_regex, merge_name_max_chars
    ):
        return True
    return _ends_with_broad_attr_name(tail, attribution_regex, merge_name_max_chars)


def _ends_with_strong_attr_name(
    tail: str, attribution_strong_regex: CompiledPattern, merge_name_max_chars: int
) -> bool:
    """Strong attribution (حدثنا...) followed by a short name without sentence-end."""
    last_strong = None
    for match in attribution_strong_regex.finditer(tail):
        last_strong = match
    if last_strong is None:
        return False
    remaining = tail[last_strong.end() :].rstrip()
    if not remaining:
        return True
    return len(remaining) <= merge_name_max_chars and not sentence_end.search(remaining)


def _ends_with_broad_attr_name(
    tail: str, attribution_regex: CompiledPattern, merge_name_max_chars: int
) -> bool:
    """Broad attribution (incl. عن) near end followed by a short name."""
    last_attr = None
    for match in attribution_regex.finditer(tail):
        last_attr = match
    if last_attr is None:
        return False
    remaining = tail[last_attr.end() :].rstrip()
    if not remaining:
        return False
    return len(remaining) <= merge_name_max_chars and not sentence_end.search(remaining)


def _is_speech_verb_to_attr_strong(
    text: str,
    next_stripped: str,
    speech_verb_tail_regex: CompiledPattern,
    attribution_strong_regex: CompiledPattern | None,
) -> bool:
    """Return True when text ends with a speech verb and next starts with ATTRIBUTION_STRONG.

    Requires ATTRIBUTION_STRONG in the current text too, so prose that
    coincidentally ends with قال is not merged.
    """
    if attribution_strong_regex is None or not speech_verb_tail_regex.search(text):
        return False
    return bool(
        attribution_strong_regex.match(next_stripped) and attribution_strong_regex.search(text)
    )


def _text_ends_with_merge_tail(text: str, cues: MergeCues) -> bool:
    """Trailing comma, speech-verb tail, or transmission-verb tail at end of text."""
    if trailing_comma.search(text) or cues.speech_verb_tail_regex.search(text):
        return True
    return cues.transmission_tail_regex is not None and bool(
        cues.transmission_tail_regex.search(text)
    )
