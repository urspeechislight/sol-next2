"""Unit tests for the segment behavior routing engine.

Lock in the routing-table logic with synthetic rules — requires / any_of /
none_of / genre_gate, priority ordering, start_threshold filtering, and the
unrouted fall-through — independent of the full config. End-to-end routing on
real config is covered by test_segment.py.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest

from backend.pipeline.errors import SegmentError
from backend.pipeline.models import Pattern
from backend.pipeline.segment import (
    parse_behavior_rules,
    route_behavior,
    validate_required_behaviors,
)
from backend.pipeline.vocab import HADITH__BEHAVIOR_GENERAL_PROSE

_GENERAL = HADITH__BEHAVIOR_GENERAL_PROSE


def _pattern(pattern_id: str, char_start: int = 0) -> Pattern:
    """A minimal Pattern at ``char_start`` (char_end is irrelevant to routing)."""
    return Pattern(
        pattern_id=pattern_id, matched_text=pattern_id, char_start=char_start, char_end=1
    )


def _rule(
    behavior_id: str,
    *,
    requires: Iterable[str] = (),
    any_of: Iterable[str] = (),
    none_of: Iterable[str] = (),
    priority: int = 0,
    genre_gate: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a raw behavior-rule config entry for parse_behavior_rules."""
    entry: dict[str, Any] = {
        "id": behavior_id,
        "requires": list(requires),
        "any_of": list(any_of),
        "none_of": list(none_of),
        "priority": priority,
    }
    if genre_gate is not None:
        entry["genre_gate"] = list(genre_gate)
    return entry


def test_should_route_to_general_prose_when_no_patterns_detected() -> None:
    rules = parse_behavior_rules([_rule("HADITH", requires=["ATTRIBUTION"], priority=1)])
    behavior, routed = route_behavior([], rules, {})
    assert behavior == _GENERAL
    assert routed is True


def test_should_route_to_matching_behavior_when_required_pattern_present() -> None:
    rules = parse_behavior_rules([_rule("HADITH", requires=["ATTRIBUTION"], priority=1)])
    behavior, routed = route_behavior([_pattern("ATTRIBUTION")], rules, {})
    assert behavior == "HADITH"
    assert routed is True


def test_should_skip_rule_when_required_pattern_absent() -> None:
    rules = parse_behavior_rules([_rule("HADITH", requires=["ATTRIBUTION"], priority=1)])
    behavior, routed = route_behavior([_pattern("OTHER")], rules, {})
    assert behavior == _GENERAL
    assert routed is False


def test_should_require_any_of_pattern_when_rule_has_any_of() -> None:
    rules = parse_behavior_rules([_rule("BIO", any_of=["BIRTH", "DEATH"], priority=1)])
    assert route_behavior([_pattern("BIRTH")], rules, {})[0] == "BIO"
    assert route_behavior([_pattern("OTHER")], rules, {})[0] == _GENERAL


def test_should_exclude_rule_when_none_of_pattern_present() -> None:
    rules = parse_behavior_rules(
        [_rule("HADITH", requires=["ATTRIBUTION"], none_of=["NARRATIVE"], priority=1)]
    )
    detected = [_pattern("ATTRIBUTION"), _pattern("NARRATIVE")]
    assert route_behavior(detected, rules, {})[0] == _GENERAL


def test_should_pass_genre_gate_only_when_book_type_matches() -> None:
    rules = parse_behavior_rules([_rule("NARR", any_of=["SIRA"], genre_gate={"sira"}, priority=1)])
    assert route_behavior([_pattern("SIRA")], rules, {}, book_type="sira")[0] == "NARR"
    assert route_behavior([_pattern("SIRA")], rules, {}, book_type="fiqh")[0] == _GENERAL


def test_should_pick_highest_priority_when_multiple_rules_match() -> None:
    rules = parse_behavior_rules(
        [
            _rule("LOW", requires=["ATTRIBUTION"], priority=1),
            _rule("HIGH", requires=["ATTRIBUTION"], priority=2),
        ]
    )
    assert route_behavior([_pattern("ATTRIBUTION")], rules, {})[0] == "HIGH"


def test_should_not_shadow_specific_rule_with_empty_requires_and_any_of() -> None:
    rules = parse_behavior_rules(
        [
            _rule("CATCHALL", priority=2),
            _rule("SPECIFIC", requires=["ATTRIBUTION"], priority=1),
        ]
    )
    assert route_behavior([_pattern("ATTRIBUTION")], rules, {})[0] == "SPECIFIC"


def test_should_return_unrouted_when_patterns_match_no_rule() -> None:
    rules = parse_behavior_rules([_rule("HADITH", requires=["ATTRIBUTION"], priority=1)])
    behavior, routed = route_behavior([_pattern("ORPHAN")], rules, {})
    assert behavior == _GENERAL
    assert routed is False


def test_should_apply_start_threshold_to_mid_span_pattern() -> None:
    rules = parse_behavior_rules([_rule("HADITH", requires=["ATTRIBUTION"], priority=1)])
    thresholds = {"ATTRIBUTION": 1}
    within = route_behavior([_pattern("ATTRIBUTION", char_start=1)], rules, thresholds)[0]
    beyond = route_behavior([_pattern("ATTRIBUTION", char_start=2)], rules, thresholds)[0]
    assert within == "HADITH"
    assert beyond == _GENERAL


def test_should_sort_parsed_rules_by_priority_descending() -> None:
    rules = parse_behavior_rules([_rule("LOW", priority=1), _rule("HIGH", priority=2)])
    assert [rule.behavior_id for rule in rules] == ["HIGH", "LOW"]


def test_should_raise_when_required_behavior_id_missing() -> None:
    with pytest.raises(SegmentError):
        validate_required_behaviors([{"id": "OTHER"}])


def test_should_pass_when_required_behavior_ids_present() -> None:
    validate_required_behaviors([{"id": _GENERAL}, {"id": "SECTION_HEADING"}])
