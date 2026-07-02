"""Phase contracts for the ported pipeline.

Declares what each ported phase requires and produces, and validates that a
manuscript meets a phase's entry requirements before it runs. Ported from
sol-next's src/contracts.py, carrying only the two phases that exist in this
codebase (segment, extract); each later phase brings its contract back with
it. Manuscript and Span are imported only under TYPE_CHECKING so this module
stays free of the model graph at runtime.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from backend.core.errors import ContractError

if TYPE_CHECKING:
    from backend.pipeline.models import Manuscript, Span


@dataclass(frozen=True)
class PhaseContract:
    """Declares the input/output contract for one pipeline phase."""

    phase_name: str
    phase_number: int
    requires: frozenset[str]
    produces: frozenset[str]


PHASE_CONTRACTS: dict[str, PhaseContract] = {
    "segment": PhaseContract(
        "segment",
        2,
        frozenset({"pages"}),
        frozenset({"spans", "spans.behavior", "spans.hierarchy"}),
    ),
    "extract": PhaseContract(
        "extract",
        3,
        frozenset({"spans", "spans.behavior", "spans.hierarchy"}),
        frozenset({"spans.entities", "spans.units"}),
    ),
}


def validate_manuscript_for_phase(manuscript: Manuscript, phase_name: str) -> None:
    """Validate that ``manuscript`` meets ``phase_name``'s entry requirements.

    Raises ContractError on the first missing requirement. The segment phase
    requires only pages; the span/behavior/hierarchy checks gate extract.
    """
    if phase_name not in PHASE_CONTRACTS:
        raise ContractError(f"Unknown phase: {phase_name}")
    contract = PHASE_CONTRACTS[phase_name]
    for requirement in sorted(contract.requires):
        if requirement == "pages":
            if not manuscript.pages:
                raise ContractError(f"Phase '{phase_name}' requires pages but manuscript has none")
        elif requirement == "spans":
            if not manuscript.spans:
                raise ContractError(f"Phase '{phase_name}' requires spans but manuscript has none")
        elif requirement == "spans.behavior":
            _require_span_field(manuscript, phase_name, requirement, lambda s: s.behavior)
        elif requirement == "spans.hierarchy":
            _require_span_field(manuscript, phase_name, requirement, lambda s: s.hierarchy)


def _require_span_field(
    manuscript: Manuscript,
    phase_name: str,
    requirement: str,
    getter: Callable[[Span], object | None],
) -> None:
    """Raise ContractError if any span still has the required field None."""
    for span in manuscript.spans:
        if getter(span) is None:
            raise ContractError(
                f"Phase '{phase_name}' requires {requirement} but span {span.span_id} has it None"
            )
