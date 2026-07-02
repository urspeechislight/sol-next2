"""Canonical PERSON entity emission — one path, one taxonomy.

Every detector that finds a person in Arabic text calls emit_person_entity. It
forces entity_type to PERSON, stores the role discriminator in
metadata.role_in_context, and validates role/source/location against closed
enums so typos can't proliferate silently. Ported from sol-next's
src/utils/persons.py with the PERSON__ constants renamed to the approved
NARRATOR__ domain; the enums carry only the members current extractors
produce, and each future extractor brings its members back with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from backend.core.constants import HADITH__ENTITY_PERSON
from backend.pipeline.config import Config
from backend.pipeline.contracts import PHASE_CONTRACTS
from backend.pipeline.models import Entity, Span, create_entity

NARRATOR__ROLE_NARRATOR: Final[str] = "narrator"
NARRATOR__ROLES_ALL: Final[frozenset[str]] = frozenset({NARRATOR__ROLE_NARRATOR})

NARRATOR__SOURCE_CHAIN_WALK: Final[str] = "chain_walk"
NARRATOR__SOURCE_ISNAD_BACK_REFERENCE: Final[str] = "isnad_back_reference"
NARRATOR__SOURCES: Final[frozenset[str]] = frozenset(
    {NARRATOR__SOURCE_CHAIN_WALK, NARRATOR__SOURCE_ISNAD_BACK_REFERENCE}
)

NARRATOR__LOCATION_BODY: Final[str] = "body"
NARRATOR__LOCATIONS: Final[frozenset[str]] = frozenset({NARRATOR__LOCATION_BODY})


@dataclass(frozen=True, slots=True)
class PersonSpec:
    """Validated role/source/provenance fields for a PERSON entity."""

    role_in_context: str
    source: str
    config: Config
    extractor_id: str
    chain_position: int | None = None
    is_relative_reference: bool = False
    location: str = NARRATOR__LOCATION_BODY
    text_source: str | None = None
    extra_metadata: dict[str, Any] | None = None
    confidence: float | None = None


def emit_person_entity(
    span: Span, text: str, char_start: int, char_end: int, spec: PersonSpec
) -> Entity:
    """Construct one PERSON entity with validated, canonical metadata.

    The validated role/source/location enums prevent silent typo proliferation,
    and the assembled metadata dict is the single contract downstream consumers
    (graph, reader) can depend on.

    Raises ValueError when role/source/location is not in its closed enum.
    """
    if spec.role_in_context not in NARRATOR__ROLES_ALL:
        raise ValueError(f"invalid role_in_context {spec.role_in_context!r}")
    if spec.source not in NARRATOR__SOURCES:
        raise ValueError(f"invalid source {spec.source!r}")
    if spec.location not in NARRATOR__LOCATIONS:
        raise ValueError(f"invalid location {spec.location!r}")

    metadata: dict[str, Any] = {
        "role_in_context": spec.role_in_context,
        "source": spec.source,
        "location": spec.location,
    }
    if spec.chain_position is not None:
        metadata["chain_position"] = spec.chain_position
    if spec.is_relative_reference:
        metadata["is_relative_reference"] = True
    if spec.extra_metadata:
        metadata.update(spec.extra_metadata)

    return create_entity(
        entity_type=HADITH__ENTITY_PERSON,
        text=text,
        char_start=char_start,
        char_end=char_end,
        span=span,
        extractor_id=spec.extractor_id,
        config=spec.config,
        phase=PHASE_CONTRACTS["extract"].phase_number,
        metadata=metadata,
        confidence=spec.confidence,
        text_source=spec.text_source,
    )
