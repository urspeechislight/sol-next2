"""Failure-budget enforcement for the segment phase's behavior routing.

When too many content spans land on GENERAL_PROSE with no explicit routing rule
matching, the routing taxonomy has stopped modelling the corpus. Continuing
produces structurally valid garbage, so segment halts. Ported from sol-next's
src/utils/failure_budget.py.
"""

from __future__ import annotations

from typing import Any

from backend.pipeline.errors import SegmentError


def enforce_failure_budget(
    config_raw: dict[str, Any],
    unclassified_count: int,
    content_span_count: int,
    manifestation_id: str,
    book_type: str | None = None,
) -> None:
    """Halt segmentation when the unrouted share exceeds the budget.

    Raises SegmentError when the required failure_budget config keys are absent,
    or once the content-span count meets the enforcement minimum and the share of
    spans routed to GENERAL_PROSE without an explicit rule exceeds the configured
    ceiling. Inputs below the minimum are skipped (a single-span fixture is not
    statistically meaningful).

    A book_type listed in ``failure_budget.exempt_book_types`` is skipped: for
    prose genres (adab / language-sciences anthologies) GENERAL_PROSE is the
    expected classification for most content, not a routing gap, so the ceiling
    calibrated on the hadith/sira track does not apply.
    """
    if content_span_count == 0:
        return
    budget = config_raw.get("failure_budget", {})
    max_pct = budget.get("unclassified_routed_max_pct")
    min_spans = budget.get("min_content_spans_for_enforcement")
    if max_pct is None or min_spans is None:
        raise SegmentError(
            "config/sol.yaml missing failure_budget.unclassified_routed_max_pct "
            "or min_content_spans_for_enforcement — segment requires both."
        )
    if book_type is not None and book_type in set(budget.get("exempt_book_types", [])):
        return
    if content_span_count < int(min_spans):
        return
    pct = 100 * unclassified_count / content_span_count
    if pct > float(max_pct):
        raise SegmentError(
            f"failure_budget exceeded for {manifestation_id}: "
            f"{unclassified_count}/{content_span_count} content spans "
            f"({pct:.2f}%) routed to GENERAL_PROSE without an explicit rule, "
            f"budget is {max_pct}%. Tighten the routing table or add a rule."
        )
