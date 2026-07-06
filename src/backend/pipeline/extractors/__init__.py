"""Phase 3 behavior-gated extractors.

Each extractor consumes a span whose behavior segment routed in Phase 2 and
produces Entity objects — primarily from its Phase 2 pattern matches, with
supplementary module-compiled scans where the phase-2 pattern table carries
no signal (the isnad boundary regexes, the matn mention shapes). The
behavior-to-extractor registry maps the extractor names in config.extractors
to their callables; each future extractor registers here when it lands,
together with its config entries.
"""

from __future__ import annotations

from collections.abc import Callable

from backend.core.constants import (
    DATE__ENTITY_HIJRI_YEAR,
    DATE__ENTITY_LUNAR_MONTH,
    EVENT__ENTITY_NAMED,
    GRAMMAR__ENTITY_TERM,
    HADITH__ENTITY_PERSON,
    QURAN__ENTITY_NAMED,
)
from backend.pipeline.config import Config
from backend.pipeline.extractors.dates import date_expression_extractor
from backend.pipeline.extractors.events import event_extractor
from backend.pipeline.extractors.grammar import grammar_term_extractor
from backend.pipeline.extractors.hadith import narrator_extractor
from backend.pipeline.extractors.mentions import person_mention_extractor
from backend.pipeline.extractors.quran_entities import quran_entity_extractor
from backend.pipeline.models import Entity, Span

type ExtractorFn = Callable[[Span, Config], list[Entity]]

VALID_ENTITY_TYPES: frozenset[str] = frozenset(
    {
        HADITH__ENTITY_PERSON,
        GRAMMAR__ENTITY_TERM,
        QURAN__ENTITY_NAMED,
        EVENT__ENTITY_NAMED,
        DATE__ENTITY_HIJRI_YEAR,
        DATE__ENTITY_LUNAR_MONTH,
    }
)

EXTRACTOR_REGISTRY: dict[str, ExtractorFn] = {
    "narrator_extractor": narrator_extractor,
    "person_mention_extractor": person_mention_extractor,
    "grammar_term_extractor": grammar_term_extractor,
    "quran_entity_extractor": quran_entity_extractor,
    "date_expression_extractor": date_expression_extractor,
    "event_extractor": event_extractor,
}
