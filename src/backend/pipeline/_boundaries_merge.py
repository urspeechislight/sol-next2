"""Isnad-continuation merge logic for the segment phase.

After the boundary splitter splits text into paragraphs, some splits are false:
an attribution verb that continues an isnad chain from the previous line (e.g.
"قال : حدثني جابر" — the حدثني is the next chain link, not a new hadith). This
module rejoins such splits. Ported from sol-next's src/utils/boundaries.py
(merge half). Compiled-pattern fields are suffixed _regex (not _re) so method
calls read as ``pattern_regex.search`` rather than colliding with a crude
``re.search`` substring grep.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.patterns import CompiledPattern
from backend.pipeline._boundaries_regex import (
    footnote_tail,
    kunya_tail,
    patronymic_tail,
    sentence_end,
    trailing_comma,
)


@dataclass(frozen=True, slots=True)
class MergeCues:
    """Config-derived regexes + thresholds for isnad-continuation merging."""

    attribution_regex: CompiledPattern | None
    isnad_tail_max_chars: int
    chain_continuation_regex: CompiledPattern | None = None
    narrative_samitu_regex: CompiledPattern | None = None
    attribution_strong_regex: CompiledPattern | None = None
    merge_name_max_chars: int = 0
    transmission_tail_regex: CompiledPattern | None = None
    isnad_continuation_regex: CompiledPattern | None = None
    speech_verb_tail_regex: CompiledPattern | None = None


@dataclass(frozen=True, slots=True)
class _MergeDecisionCues:
    """Narrowed (non-None) merge cues for one per-pair merge decision."""

    attribution_regex: CompiledPattern
    isnad_tail_max_chars: int
    chain_continuation_regex: CompiledPattern
    narrative_samitu_regex: CompiledPattern
    isnad_continuation_regex: CompiledPattern
    speech_verb_tail_regex: CompiledPattern
    attribution_strong_regex: CompiledPattern | None = None
    merge_name_max_chars: int = 0
    transmission_tail_regex: CompiledPattern | None = None


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


def _text_ends_with_merge_tail(text: str, cues: _MergeDecisionCues) -> bool:
    """Trailing comma, speech-verb tail, or transmission-verb tail at end of text."""
    if trailing_comma.search(text) or cues.speech_verb_tail_regex.search(text):
        return True
    return cues.transmission_tail_regex is not None and bool(
        cues.transmission_tail_regex.search(text)
    )


def _should_merge_next(text: str, next_text: str, cues: _MergeDecisionCues) -> bool:
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


def merge_isnad_continuations(
    paragraphs: list[tuple[str, int, int]],
    cues: MergeCues,
) -> list[tuple[str, int, int]]:
    """Merge consecutive paragraphs where an attribution verb continues an isnad chain.

    Merges the seven classes of false splits decided by _should_merge_next. When
    cues.attribution_regex is None (genre has no attribution) there is nothing to
    merge. All regex cues are built from config at startup.
    """
    if cues.attribution_regex is None:
        return paragraphs
    if (
        cues.chain_continuation_regex is None
        or cues.narrative_samitu_regex is None
        or cues.isnad_continuation_regex is None
        or cues.speech_verb_tail_regex is None
    ):
        return _merge_speech_verb_only(
            paragraphs, cues.attribution_regex, cues.isnad_continuation_regex
        )
    decision_cues = _MergeDecisionCues(
        cues.attribution_regex,
        cues.isnad_tail_max_chars,
        cues.chain_continuation_regex,
        cues.narrative_samitu_regex,
        cues.isnad_continuation_regex,
        cues.speech_verb_tail_regex,
        cues.attribution_strong_regex,
        cues.merge_name_max_chars,
        cues.transmission_tail_regex,
    )
    return _merge_with_full_cues(paragraphs, decision_cues)


def _merge_with_full_cues(
    paragraphs: list[tuple[str, int, int]], cues: _MergeDecisionCues
) -> list[tuple[str, int, int]]:
    """Merge using the full cue set (all narrator_extraction regexes present)."""
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


def _merge_speech_verb_only(
    paragraphs: list[tuple[str, int, int]],
    attribution_regex: CompiledPattern,
    isnad_continuation_regex: CompiledPattern | None = None,
) -> list[tuple[str, int, int]]:
    """Merge using only the speech-verb continuation condition.

    Used when the narrator_extraction config section is absent, so only the
    isnad_continuation + attribution pair is available.
    """
    if isnad_continuation_regex is None:
        return paragraphs
    merged: list[tuple[str, int, int]] = []
    i = 0
    while i < len(paragraphs):
        text, pg_start, pg_end = paragraphs[i]
        while (
            i + 1 < len(paragraphs)
            and isnad_continuation_regex.search(text)
            and attribution_regex.match(paragraphs[i + 1][0].lstrip())
        ):
            next_text, _, next_pg_end = paragraphs[i + 1]
            text = text + "\n" + next_text
            pg_end = next_pg_end
            i += 1
        merged.append((text, pg_start, pg_end))
        i += 1
    return merged
