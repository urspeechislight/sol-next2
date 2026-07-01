"""Phase 3 behavior-gated extractors.

Each extractor consumes a span whose behavior segment routed in Phase 2 and
produces Entity objects from its Phase 2 pattern matches — it never re-scans
span.text. The behavior-to-extractor registry maps the extractor names in
config.extractors to their callables; the hadith narrator extractor is the only
real implementation in this port, and every other referenced name resolves to a
no-op stub until its extractor lands.
"""

from __future__ import annotations

from collections.abc import Callable

from backend.core.constants import HADITH__ENTITY_PERSON
from backend.pipeline.config import Config
from backend.pipeline.extractors.hadith import narrator_extractor
from backend.pipeline.models import Entity, Span

type ExtractorFn = Callable[[Span, Config], list[Entity]]

VALID_ENTITY_TYPES: frozenset[str] = frozenset({HADITH__ENTITY_PERSON})


def _no_op_extractor(_span: Span, _config: Config) -> list[Entity]:
    """Return no entities — placeholder for extractors not yet ported."""
    return []


EXTRACTOR_REGISTRY: dict[str, ExtractorFn] = {
    "narrator_extractor": narrator_extractor,
    "quran_verse_extractor": _no_op_extractor,
    "citation_extractor": _no_op_extractor,
    "date_expression_extractor": _no_op_extractor,
    "gazetteer_person_extractor": _no_op_extractor,
    "ner_person_extractor": _no_op_extractor,
    "person_extractor": _no_op_extractor,
    "date_extractor": _no_op_extractor,
    "rijal_entry_extractor": _no_op_extractor,
    "theme_extractor": _no_op_extractor,
}
