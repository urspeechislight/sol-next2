"""Atomicizer strategies for the extract phase.

Split a span into atomic units: whole_span (one unit covering the span) or
sanad_matn_split (an ISNAD unit + a MATN unit at the precomputed isnad_end, with a
whole-span reserve unit when the split yields an empty side). Ported from
sol-next's src/phases/extract.py atomicizer half, split out to keep the extract
orchestrator under the size cap.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.core.constants import (
    HADITH__STRATEGY_SANAD_MATN,
    HADITH__STRATEGY_WHOLE_SPAN,
    HADITH__UNIT_FOOTNOTE,
    HADITH__UNIT_ID_FORMAT,
)
from backend.core.errors import ExtractError
from backend.core.logging import get_logger
from backend.pipeline.models import HierarchyPath, Span, Unit
from backend.pipeline.text import strip_footnote_markers

_logger = get_logger("shia-library.pipeline.extract")


@dataclass(frozen=True, slots=True)
class AtomizeArgs:
    """Config-derived context for an atomicizer strategy function."""

    config_rule: dict[str, Any]
    manifestation_id: str
    behavior: str
    hierarchy: HierarchyPath


def atomicize_span(span: Span, start_index: int, args: AtomizeArgs, strategy: str) -> list[Unit]:
    """Dispatch the configured atomicizer strategy, raising on an unknown one."""
    if strategy == HADITH__STRATEGY_WHOLE_SPAN:
        return _atomicize_whole_span(span, start_index, args)
    if strategy == HADITH__STRATEGY_SANAD_MATN:
        return _atomicize_sanad_matn(span, start_index, args)
    raise ExtractError(f"Unknown atomicizer strategy: {strategy}")


def _text_from_pattern(span: Span, pattern_id: str) -> str:
    """Return the first match of pattern_id, else the full span text.

    When a structural span's content IS the pattern match (e.g. BASMALA), the unit
    text is the matched text rather than the full span, which may carry inter-
    boundary noise.
    """
    for pattern in span.patterns:
        if pattern.pattern_id == pattern_id:
            return pattern.matched_text.strip()
    return span.text.strip()


def _atomicize_whole_span(span: Span, start_index: int, args: AtomizeArgs) -> list[Unit]:
    """One unit covering the whole span; optionally retext from a pattern match."""
    unit_type: str = args.config_rule["unit_type"]
    unit_id = HADITH__UNIT_ID_FORMAT.format(
        manifestation_id=args.manifestation_id, index=start_index
    )
    unit_metadata: dict[str, Any] = {}
    refers_to = span.metadata.get("refers_to_span_id")
    if refers_to is not None:
        unit_metadata["refers_to_span_id"] = refers_to
    pattern_id = args.config_rule.get("use_pattern_text")
    if pattern_id is not None:
        text_ar = _text_from_pattern(span, pattern_id)
        span.text = text_ar
    else:
        text_ar = strip_footnote_markers(span.text)
    return [
        Unit(
            unit_id=unit_id,
            text_ar=text_ar,
            unit_type=unit_type,
            behavior=args.behavior,
            span_id=span.span_id,
            page_start=span.page_start,
            page_end=span.page_end,
            hierarchy=args.hierarchy,
            metadata=unit_metadata,
        )
    ]


def _atomicize_sanad_matn(span: Span, start_index: int, args: AtomizeArgs) -> list[Unit]:
    """Split the span into ISNAD + MATN units at isnad_end, else one reserve unit.

    When the split produces an empty isnad or matn side, the configured reserve
    unit type covers the whole span so the span never ends up unit-less.
    """
    isnad_end = span.metadata["isnad_end"]
    if isnad_end < len(span.text):
        isnad_text = strip_footnote_markers(span.text[:isnad_end])
        matn_text = strip_footnote_markers(span.text[isnad_end:])
        if isnad_text and matn_text:
            unit_types: dict[str, Any] = args.config_rule["unit_types"]
            return [
                _unit(
                    span,
                    args,
                    HADITH__UNIT_ID_FORMAT.format(
                        manifestation_id=args.manifestation_id, index=start_index
                    ),
                    isnad_text,
                    unit_types["isnad"],
                ),
                _unit(
                    span,
                    args,
                    HADITH__UNIT_ID_FORMAT.format(
                        manifestation_id=args.manifestation_id, index=start_index + 1
                    ),
                    matn_text,
                    unit_types["matn"],
                ),
            ]
        _logger.warning("sanad_matn_empty_split", span_id=span.span_id, isnad_end=isnad_end)

    reserve_type: str = args.config_rule["fallback_unit_type"]
    reserve_id = HADITH__UNIT_ID_FORMAT.format(
        manifestation_id=args.manifestation_id, index=start_index
    )
    return [_unit(span, args, reserve_id, strip_footnote_markers(span.text), reserve_type)]


def _unit(span: Span, args: AtomizeArgs, unit_id: str, text_ar: str, unit_type: str) -> Unit:
    """Build one Unit anchored on the span with the shared args context."""
    return Unit(
        unit_id=unit_id,
        text_ar=text_ar,
        unit_type=unit_type,
        behavior=args.behavior,
        span_id=span.span_id,
        page_start=span.page_start,
        page_end=span.page_end,
        hierarchy=args.hierarchy,
    )


def make_footnote_unit(
    unit_id: str, footnote_text: str, behavior: str, hierarchy: HierarchyPath, span: Span
) -> Unit:
    """Build one FOOTNOTE_UNIT from a footnote entry."""
    return Unit(
        unit_id=unit_id,
        text_ar=footnote_text,
        unit_type=HADITH__UNIT_FOOTNOTE,
        behavior=behavior,
        span_id=span.span_id,
        page_start=span.page_start,
        page_end=span.page_end,
        hierarchy=hierarchy,
    )
