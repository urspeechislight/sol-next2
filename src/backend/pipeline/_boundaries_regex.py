"""Regex builders for isnad-continuation merge detection (segment phase).

The boundary splitter's lookaheads fire incorrectly when an attribution verb
continues an isnad chain from the previous line. These builders compile the
config-driven regexes the merge step uses to detect and rejoin such false
splits. Ported from sol-next's src/utils/boundaries.py (builder half). Every
regex compiles through backend.patterns (CENTRAL-002); callers never import re.

The tail/end regexes are lowercase module locals (not UPPER constants) so a
later ``.search``/``.sub`` call does not collide with a crude ``re.search``/
``re.sub`` substring grep in the legacy hook.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from backend.patterns import (
    CompiledPattern,
    cached_compile,
    cached_compile_alternation,
    escape_pattern,
)

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


def build_merge_params_from_config(
    config_raw: dict[str, Any],
    patterns: list[dict[str, Any]],
) -> tuple[
    CompiledPattern | None,
    CompiledPattern | None,
    CompiledPattern | None,
    CompiledPattern | None,
    CompiledPattern | None,
]:
    """Build all merge regexes from config for merge_isnad_continuations.

    Reads narrator_extraction word lists and the SPEECH_VERB_GENERIC pattern.
    Returns (None, None, None, None, None) when narrator_extraction is absent
    (non-hadith genres) or SPEECH_VERB_GENERIC is missing.
    """
    ncfg = config_raw.get("narrator_extraction")
    if ncfg is None:
        return None, None, None, None, None
    tail_verbs = ncfg.get("transmission_tail_verbs", [])
    trans_regex = build_transmission_tail_re(tail_verbs) if tail_verbs else None
    speech_verb_entry = next((p for p in patterns if p["id"] == "SPEECH_VERB_GENERIC"), None)
    if speech_verb_entry is None:
        return None, None, None, None, None
    isnad_cont_regex, speech_tail_regex = _build_speech_verb_res(speech_verb_entry["regex"])
    return (
        build_chain_continuation_re(ncfg["prepositional_an_exclusions"]),
        build_narrative_samitu_re(ncfg["narrative_context_words"]),
        trans_regex,
        isnad_cont_regex,
        speech_tail_regex,
    )
