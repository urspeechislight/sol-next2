"""Canonical PERSON entity emission — one path, one taxonomy.

Every detector that finds a person in Arabic text calls emit_person_entity. It
forces entity_type to PERSON, stores the role discriminator in
metadata.role_in_context, and validates role/source/location against closed
enums so typos can't proliferate silently. Ported from sol-next's
src/utils/persons.py; the PERSON__ constants are renamed to the approved
NARRATOR__ domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from backend.core.constants import HADITH__ENTITY_PERSON
from backend.pipeline.config import Config
from backend.pipeline.contracts import PHASE_CONTRACTS
from backend.pipeline.models import Entity, EntityInputs, Span, create_entity

NARRATOR__ROLE_NARRATOR: Final[str] = "narrator"
NARRATOR__ROLE_PROTAGONIST: Final[str] = "protagonist"
NARRATOR__ROLE_CITED_SCHOLAR: Final[str] = "cited_scholar"
NARRATOR__ROLE_TEACHER: Final[str] = "teacher"
NARRATOR__ROLE_STUDENT: Final[str] = "student"
NARRATOR__ROLE_ENTRY_SUBJECT: Final[str] = "entry_subject"
NARRATOR__ROLE_BIOGRAPHY_SUBJECT: Final[str] = "biography_subject"
NARRATOR__ROLE_MENTIONED: Final[str] = "mentioned"
NARRATOR__ROLE_NER_INFERRED: Final[str] = "ner_inferred"
NARRATOR__ROLE_PROPHET: Final[str] = "prophet"
NARRATOR__ROLE_WIFE: Final[str] = "wife"
NARRATOR__ROLE_FAMILY: Final[str] = "family"
NARRATOR__ROLE_COMPANION: Final[str] = "companion"
NARRATOR__ROLE_CALIPH: Final[str] = "caliph"
NARRATOR__ROLE_CLASSICAL_SCHOLAR: Final[str] = "classical_scholar"
NARRATOR__ROLE_MODERN_SCHOLAR: Final[str] = "modern_scholar"
NARRATOR__ROLE_ORIENTALIST: Final[str] = "orientalist"
NARRATOR__ROLE_GROUP: Final[str] = "group"

NARRATOR__ROLES_HADITH: Final[frozenset[str]] = frozenset(
    {
        NARRATOR__ROLE_NARRATOR,
        NARRATOR__ROLE_PROTAGONIST,
        NARRATOR__ROLE_CITED_SCHOLAR,
        NARRATOR__ROLE_GROUP,
    }
)
NARRATOR__GAZETTEER_ROLES: Final[frozenset[str]] = frozenset(
    {
        NARRATOR__ROLE_PROPHET,
        NARRATOR__ROLE_WIFE,
        NARRATOR__ROLE_FAMILY,
        NARRATOR__ROLE_COMPANION,
        NARRATOR__ROLE_CALIPH,
        NARRATOR__ROLE_CLASSICAL_SCHOLAR,
        NARRATOR__ROLE_MODERN_SCHOLAR,
        NARRATOR__ROLE_ORIENTALIST,
        NARRATOR__ROLE_GROUP,
    }
)
NARRATOR__ROLES_ALL: Final[frozenset[str]] = (
    NARRATOR__ROLES_HADITH
    | NARRATOR__GAZETTEER_ROLES
    | frozenset(
        {
            NARRATOR__ROLE_TEACHER,
            NARRATOR__ROLE_STUDENT,
            NARRATOR__ROLE_ENTRY_SUBJECT,
            NARRATOR__ROLE_BIOGRAPHY_SUBJECT,
            NARRATOR__ROLE_MENTIONED,
            NARRATOR__ROLE_NER_INFERRED,
        }
    )
)

NARRATOR__SOURCE_CHAIN_WALK: Final[str] = "chain_walk"
NARRATOR__SOURCE_HONORIFIC: Final[str] = "honorific"
NARRATOR__SOURCE_PATRONYMIC: Final[str] = "patronymic"
NARRATOR__SOURCE_VERB_ANCHOR: Final[str] = "verb_anchor"
NARRATOR__SOURCE_RIJAL_NAME_REGION: Final[str] = "rijal_name_region"
NARRATOR__SOURCE_GAZETTEER: Final[str] = "gazetteer"
NARRATOR__SOURCE_NER: Final[str] = "ner"
NARRATOR__SOURCE_ISNAD_BACK_REFERENCE: Final[str] = "isnad_back_reference"

NARRATOR__SOURCES: Final[frozenset[str]] = frozenset(
    {
        NARRATOR__SOURCE_CHAIN_WALK,
        NARRATOR__SOURCE_HONORIFIC,
        NARRATOR__SOURCE_PATRONYMIC,
        NARRATOR__SOURCE_VERB_ANCHOR,
        NARRATOR__SOURCE_RIJAL_NAME_REGION,
        NARRATOR__SOURCE_GAZETTEER,
        NARRATOR__SOURCE_NER,
        NARRATOR__SOURCE_ISNAD_BACK_REFERENCE,
    }
)

NARRATOR__LOCATION_BODY: Final[str] = "body"
NARRATOR__LOCATION_FOOTNOTE: Final[str] = "footnote"
NARRATOR__LOCATIONS: Final[frozenset[str]] = frozenset(
    {NARRATOR__LOCATION_BODY, NARRATOR__LOCATION_FOOTNOTE}
)


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
        EntityInputs(
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
    )


NARRATOR__CORE_ENTITY_TYPES: Final[frozenset[str]] = frozenset({HADITH__ENTITY_PERSON})
