"""Behavior routing table for the segment phase.

Each paragraph's detected patterns are evaluated against the config behavior
table (priority-sorted) to assign a behavior label. A start_threshold on a
pattern restricts it to span-initial matches, keeping polysemous keywords that
appear mid-span from firing rules meant for span-initial occurrences.

Ported from sol-next's src/phases/segment.py (the routing half), split out so
segment.py stays under the file-size cap. No regex machinery lives here:
patterns arrive already compiled from the central pattern module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.core.constants import (
    HADITH__BEHAVIOR_GENERAL_PROSE,
    HADITH__BEHAVIOR_SECTION_HEADING,
)
from backend.core.errors import SegmentError
from backend.core.logging import get_logger
from backend.pipeline.models import Pattern

_logger = get_logger("shia-library.segment-routing")


@dataclass(frozen=True, slots=True)
class BehaviorRule:
    """A pre-parsed behavior routing rule from config."""

    behavior_id: str
    requires: frozenset[str]
    any_of: frozenset[str]
    none_of: frozenset[str]
    priority: int
    genre_gate: frozenset[str] | None = None


def parse_behavior_rules(raw_behaviors: list[dict[str, Any]]) -> list[BehaviorRule]:
    """Parse behavior routing rules from config, sorted by priority descending."""
    rules: list[BehaviorRule] = []
    for entry in raw_behaviors:
        gate_raw = entry.get("genre_gate")
        rules.append(
            BehaviorRule(
                behavior_id=entry["id"],
                requires=frozenset(entry.get("requires", [])),
                any_of=frozenset(entry.get("any_of", [])),
                none_of=frozenset(entry.get("none_of", [])),
                priority=entry.get("priority", 0),
                genre_gate=frozenset(gate_raw) if gate_raw else None,
            )
        )
    rules.sort(key=lambda rule: rule.priority, reverse=True)
    return rules


def parse_start_thresholds(raw_patterns: list[dict[str, Any]]) -> dict[str, int]:
    """Extract start_threshold values: pattern_id -> max char_start for routing.

    A start_threshold on a pattern means it only counts for behavior routing when
    its earliest match starts within that many characters of the span's start.
    """
    thresholds: dict[str, int] = {}
    for entry in raw_patterns:
        if "start_threshold" in entry:
            thresholds[entry["id"]] = int(entry["start_threshold"])
    return thresholds


def route_behavior(
    detected_patterns: list[Pattern],
    behavior_rules: list[BehaviorRule],
    start_thresholds: dict[str, int],
    book_type: str | None = None,
) -> tuple[str, bool]:
    """Route detected patterns to a behavior label via the routing table.

    Evaluates rules in priority order (highest first). A rule matches when all
    requires are present, at least one any_of is present (if non-empty), none of
    none_of are present, and genre_gate passes (if set). Returns (label,
    routed_explicitly): routed_explicitly is True when either no patterns were
    detected (the clean default to GENERAL_PROSE) or a configured rule matched;
    it is False only when patterns were detected but no rule matched — the
    unrouted case the failure budget tracks.
    """
    detected_ids = _thresholded_pattern_ids(detected_patterns, start_thresholds)
    if not detected_ids:
        return HADITH__BEHAVIOR_GENERAL_PROSE, True
    for rule in behavior_rules:
        if not rule.requires and not rule.any_of:
            continue
        if rule.genre_gate is not None and (book_type is None or book_type not in rule.genre_gate):
            continue
        if rule.requires and not rule.requires.issubset(detected_ids):
            continue
        if rule.any_of and not rule.any_of.intersection(detected_ids):
            continue
        if rule.none_of and rule.none_of.intersection(detected_ids):
            continue
        return rule.behavior_id, True
    _logger.warning(
        "no-behavior-rule-matched",
        pattern_ids=sorted(detected_ids),
        behavior=HADITH__BEHAVIOR_GENERAL_PROSE,
    )
    return HADITH__BEHAVIOR_GENERAL_PROSE, False


def _thresholded_pattern_ids(
    detected_patterns: list[Pattern], start_thresholds: dict[str, int]
) -> set[str]:
    """Apply start_thresholds and return the pattern ids eligible for routing."""
    if not start_thresholds:
        return {pattern.pattern_id for pattern in detected_patterns}
    earliest: dict[str, int] = {}
    for pattern in detected_patterns:
        if pattern.pattern_id not in earliest or pattern.char_start < earliest[pattern.pattern_id]:
            earliest[pattern.pattern_id] = pattern.char_start
    eligible: set[str] = set()
    for pattern_id, position in earliest.items():
        threshold = start_thresholds.get(pattern_id)
        if threshold is not None and position > threshold:
            continue
        eligible.add(pattern_id)
    return eligible


def validate_required_behaviors(raw_behaviors: list[dict[str, Any]]) -> None:
    """Validate that segment's built-in behavior ids exist in config.

    Segment references GENERAL_PROSE and SECTION_HEADING by name. If either is
    missing from config, routing and hierarchy tracking malfunction.

    Raises SegmentError if a required behavior id is missing from config.
    """
    behavior_ids = {entry["id"] for entry in raw_behaviors}
    required = {HADITH__BEHAVIOR_GENERAL_PROSE, HADITH__BEHAVIOR_SECTION_HEADING}
    missing = required - behavior_ids
    if missing:
        raise SegmentError(
            f"Config missing behavior ids {sorted(missing)}; segment needs {sorted(required)}"
        ) from None
