"""Tests for the segment phase gates: the failure budget and the phase contract.

The failure budget halts segmentation when too many content spans land on
GENERAL_PROSE without an explicit routing rule; the phase contract blocks a
manuscript that lacks the segment entry requirement (pages). Both must fail loud.
"""

from __future__ import annotations

from typing import Any

import pytest

from backend.pipeline.contracts import validate_manuscript_for_phase
from backend.pipeline.errors import ContractError, SegmentError
from backend.pipeline.failure_budget import enforce_failure_budget
from backend.pipeline.models import Manuscript, ManuscriptPage


def _budget_cfg(
    *, max_pct: float, min_spans: int, exempt: list[str] | None = None
) -> dict[str, Any]:
    """A failure_budget config block with both required keys."""
    block: dict[str, Any] = {
        "unclassified_routed_max_pct": max_pct,
        "min_content_spans_for_enforcement": min_spans,
    }
    if exempt is not None:
        block["exempt_book_types"] = exempt
    return {"failure_budget": block}


def test_should_skip_failure_budget_when_content_span_count_is_zero() -> None:
    enforce_failure_budget(
        _budget_cfg(max_pct=0, min_spans=2),
        unclassified_count=1,
        content_span_count=0,
        manifestation_id="m1",
    )


def test_should_skip_failure_budget_when_below_min_content_spans() -> None:
    enforce_failure_budget(
        _budget_cfg(max_pct=0, min_spans=2),
        unclassified_count=1,
        content_span_count=1,
        manifestation_id="m1",
    )


def test_should_raise_when_unrouted_share_exceeds_budget() -> None:
    with pytest.raises(SegmentError):
        enforce_failure_budget(
            _budget_cfg(max_pct=0, min_spans=2),
            unclassified_count=2,
            content_span_count=2,
            manifestation_id="m1",
        )


def test_should_skip_failure_budget_when_book_type_exempt() -> None:
    enforce_failure_budget(
        _budget_cfg(max_pct=0, min_spans=2, exempt=["arabic-language-sciences"]),
        unclassified_count=2,
        content_span_count=2,
        manifestation_id="m1",
        book_type="arabic-language-sciences",
    )


def test_should_not_raise_when_unrouted_share_within_budget() -> None:
    enforce_failure_budget(
        _budget_cfg(max_pct=0, min_spans=2),
        unclassified_count=0,
        content_span_count=2,
        manifestation_id="m1",
    )


def test_should_raise_when_failure_budget_config_keys_missing() -> None:
    with pytest.raises(SegmentError):
        enforce_failure_budget(
            {}, unclassified_count=1, content_span_count=2, manifestation_id="m1"
        )


def test_should_raise_contract_when_manuscript_lacks_pages() -> None:
    manuscript = Manuscript(work_id="w1", manifestation_id="m1")
    with pytest.raises(ContractError):
        validate_manuscript_for_phase(manuscript, "segment")


def test_should_pass_contract_when_manuscript_has_pages() -> None:
    manuscript = Manuscript(
        work_id="w1",
        manifestation_id="m1",
        pages=[ManuscriptPage(page_number=1, page_name="1", text="text")],
    )
    validate_manuscript_for_phase(manuscript, "segment")
