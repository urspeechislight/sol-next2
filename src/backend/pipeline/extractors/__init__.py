"""Phase 3 behavior-gated extractors.

Each extractor consumes a span whose behavior segment routed in Phase 2 and
produces Entity objects from its Phase 2 pattern matches — it never re-scans
span.text. The behavior-to-extractor registry maps the extractor names in
config.extractors to their callables. The hadith narrator extractor is the
only extractor in this port; each future extractor registers here when it
lands, together with its config entries.
"""

from __future__ import annotations

from collections.abc import Callable

from backend.core.constants import HADITH__ENTITY_PERSON
from backend.pipeline.config import Config
from backend.pipeline.extractors.hadith import narrator_extractor
from backend.pipeline.models import Entity, Span

type ExtractorFn = Callable[[Span, Config], list[Entity]]

VALID_ENTITY_TYPES: frozenset[str] = frozenset({HADITH__ENTITY_PERSON})

EXTRACTOR_REGISTRY: dict[str, ExtractorFn] = {
    "narrator_extractor": narrator_extractor,
}
