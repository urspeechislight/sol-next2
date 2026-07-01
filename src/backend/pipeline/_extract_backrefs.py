"""Isnad back-reference handling for the extract phase.

When a hadith opens with "وبهذا الاسناد" (and with this isnad), the narrator
chain from a previous hadith applies but is not written out. This copies the
source span's ISNAD unit and narrator entities onto the back-reference span,
annotating the copies with provenance metadata for later graph linking. Ported
from sol-next's src/phases/extract.py back-reference half.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from backend.core.constants import (
    HADITH__ENTITY_ID_FORMAT,
    HADITH__UNIT_ID_FORMAT,
    HADITH__UNIT_ISNAD,
)
from backend.core.logging import get_logger
from backend.pipeline.extractors.hadith import get_narrator_entities
from backend.pipeline.models import Entity, Manuscript, Span, Unit
from backend.pipeline.persons import (
    NARRATOR__ROLE_NARRATOR,
    NARRATOR__SOURCE_ISNAD_BACK_REFERENCE,
    PersonSpec,
    emit_person_entity,
)

if TYPE_CHECKING:
    from backend.pipeline.config import Config

_logger = get_logger("shia-library.pipeline.extract")


def handle_isnad_back_references(manuscript: Manuscript, unit_counter: int, config: Config) -> int:
    """Copy source ISNAD units + narrator entities onto back-reference spans.

    Returns the unit counter advanced past every back-reference unit created.
    """
    span_map = {span.span_id: span for span in manuscript.spans}
    manifestation_id = manuscript.manifestation_id
    for span in manuscript.spans:
        if not span.metadata.get("isnad_back_ref"):
            continue
        source_span_id = span.metadata.get("refers_to_span_id")
        if source_span_id is None:
            _logger.warning("isnad_back_ref_missing_source", span_id=span.span_id)
            continue
        source_span = span_map.get(source_span_id)
        if source_span is None or source_span.units is None:
            _logger.warning(
                "isnad_back_ref_source_unitless",
                span_id=span.span_id,
                source_span_id=source_span_id,
            )
            continue
        source_isnad = next(
            (unit for unit in source_span.units if unit.unit_type == HADITH__UNIT_ISNAD),
            None,
        )
        if source_isnad is None:
            continue
        behavior = span.behavior
        hierarchy = span.hierarchy
        if behavior is None or hierarchy is None:
            continue
        back_ref_unit = Unit(
            unit_id=HADITH__UNIT_ID_FORMAT.format(
                manifestation_id=manifestation_id, index=unit_counter
            ),
            text_ar=source_isnad.text_ar,
            unit_type=HADITH__UNIT_ISNAD,
            behavior=behavior,
            span_id=span.span_id,
            page_start=span.page_start,
            page_end=span.page_end,
            hierarchy=hierarchy,
            metadata={
                "isnad_source": "back_reference",
                "source_span_id": source_span_id,
                "source_unit_id": source_isnad.unit_id,
            },
        )
        unit_counter += 1
        if span.units is not None:
            span.units.insert(0, back_ref_unit)
        else:
            span.units = [back_ref_unit]
        _attach_back_ref_entities(span, source_span, config)
    return unit_counter


def _attach_back_ref_entities(span: Span, source_span: Span, config: Config) -> None:
    """Copy the source's narrator entities onto the back-reference span."""
    narrator_entities = get_narrator_entities(source_span)
    existing_count = len(span.entities) if span.entities else 0
    copied: list[Entity] = []
    for idx, src_entity in enumerate(narrator_entities):
        new_entity = emit_person_entity(
            span=source_span,
            text=src_entity.text,
            char_start=src_entity.char_start,
            char_end=src_entity.char_end,
            spec=PersonSpec(
                role_in_context=NARRATOR__ROLE_NARRATOR,
                source=NARRATOR__SOURCE_ISNAD_BACK_REFERENCE,
                config=config,
                extractor_id="isnad_back_reference",
                chain_position=src_entity.metadata.get("chain_position", idx),
                extra_metadata={
                    "isnad_source": "back_reference",
                    "source_span_id": source_span.span_id,
                    "source_entity_id": src_entity.entity_id,
                },
            ),
        )
        new_entity.entity_id = HADITH__ENTITY_ID_FORMAT.format(
            span_id=span.span_id, index=existing_count + idx
        )
        copied.append(new_entity)
    if span.entities is None:
        span.entities = copied
    else:
        span.entities.extend(copied)
