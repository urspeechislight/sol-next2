"""Date-expression extractor: hijri years and lunar months (Phase 3).

A deterministic extractor that turns the HIJRI_YEAR and LUNAR_MONTH patterns
segment already detected on a span into HIJRI_YEAR / LUNAR_MONTH entities. It
consumes ``span.patterns`` — it does not re-scan the text — so it fires exactly
where the phase-2 detectors fired. These are the free-floating date anchors that
sīra and tārīkh narrative places events against; the event extractor reads a
verse's nearby HIJRI_YEAR to date an event.

The entity text is the exact matched slice (offsets bound it in the source),
while the canonical value goes in metadata: ``year`` carries the hijri year with
Arabic-Indic digits normalized to Western form, so the graph can align "سنة ٥ هـ"
and "سنة 5 هـ" as the same year.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from backend.core.constants import DATE__ENTITY_HIJRI_YEAR, DATE__ENTITY_LUNAR_MONTH
from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.contracts import PHASE_CONTRACTS
from backend.pipeline.models import Entity, Pattern, Span, create_entity

if TYPE_CHECKING:
    from backend.pipeline.config import Config

DATE__YEAR_KEY: Final[str] = "year"

_EXTRACTOR_ID: Final[str] = "date_expression_extractor"
_DIGITS: Final[CompiledPattern] = cached_compile(r"[٠-٩0-9]{1,4}")
_DIGIT_MAP: Final[dict[int, int]] = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def _hijri_year(text: str) -> str | None:
    """The first digit run in ``text``, normalized to Western digits, or None."""
    match = _DIGITS.search(text)
    if match is None:
        return None
    return match.group(0).translate(_DIGIT_MAP)


def _date_entity(
    span: Span, config: Config, pattern: Pattern, entity_type: str, metadata: dict[str, Any]
) -> Entity:
    """Build one date entity anchored to the exact matched slice of the span."""
    return create_entity(
        entity_type=entity_type,
        text=span.text[pattern.char_start : pattern.char_end],
        char_start=pattern.char_start,
        char_end=pattern.char_end,
        span=span,
        extractor_id=_EXTRACTOR_ID,
        config=config,
        phase=PHASE_CONTRACTS["extract"].phase_number,
        metadata=metadata,
    )


def date_expression_extractor(span: Span, config: Config) -> list[Entity]:
    """Emit a HIJRI_YEAR or LUNAR_MONTH entity per date pattern segment detected.

    A HIJRI_YEAR whose match carries no parseable digit run is dropped rather
    than emitted without a normalized year. A LUNAR_MONTH is emitted as-is; its
    matched text is the month name.
    """
    entities: list[Entity] = []
    for pattern in span.patterns:
        if pattern.pattern_id == DATE__ENTITY_HIJRI_YEAR:
            year = _hijri_year(pattern.matched_text)
            if year is None:
                continue
            entities.append(
                _date_entity(span, config, pattern, DATE__ENTITY_HIJRI_YEAR, {DATE__YEAR_KEY: year})
            )
        elif pattern.pattern_id == DATE__ENTITY_LUNAR_MONTH:
            entities.append(_date_entity(span, config, pattern, DATE__ENTITY_LUNAR_MONTH, {}))
    return entities
