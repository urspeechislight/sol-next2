"""Named-entity extractor for Qurʾānic text (Phase 3).

Where the narrator extractor models a hadith's chain and the grammar extractor
the vocabulary of naḥw, this extractor names the Qurʾān's own dramatis personae:
prophets, other persons, angels, peoples, places, revealed scriptures, and the
idols. It emits one QURAN_ENTITY per mention, categorized, so a later graph can
be built from the Qurʾān's own text — every verse that names موسى, every passage
that speaks of ثمود.

Matching runs through the shared ``gazetteer_match`` primitives (fold, clitic,
accusative alif, offset-exact). Several names coincide with a common word;
rather than a morphological guess (CAMeL has no proper-noun reading for عاد or
صالح at all), each such name carries a deterministic preceding-word rule
validated against every Qurʾānic occurrence: ``entity_prev`` keeps the name only
after a listed word (صالح after أخاهم/يا/قوم), and ``common_prev`` drops it after
a listed word (عاد after لا/من/حتى). A name with neither rule is always kept.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from backend.core.constants import (
    ENTITY__BOOK_TYPE_KEY,
    ENTITY__CATEGORY_KEY,
    ENTITY__NAME_KEY,
    QURAN__ENTITY_NAMED,
)
from backend.pipeline.contracts import PHASE_CONTRACTS
from backend.pipeline.gazetteer_match import Matcher, compile_matchers, scan_gazetteer
from backend.pipeline.models import Entity, Span, create_entity

if TYPE_CHECKING:
    from backend.pipeline.config import Config

_CONFIG_SECTION: Final[str] = "quran_extraction"

_MATCHER_CACHE: dict[int, list[Matcher[tuple[str, str]]]] = {}


def _matchers(config: Config) -> list[Matcher[tuple[str, str]]]:
    """The compiled Qurʾān gazetteer for this config, cached; payload is (category, name)."""
    gazetteer: dict[str, list[dict[str, Any]]] = config.raw.get(_CONFIG_SECTION, {}).get(
        "gazetteer", {}
    )
    key = id(gazetteer)
    if key not in _MATCHER_CACHE:
        _MATCHER_CACHE[key] = compile_matchers(
            gazetteer, lambda category, entry: (category, entry[ENTITY__NAME_KEY])
        )
    return _MATCHER_CACHE[key]


def quran_entity_extractor(span: Span, config: Config) -> list[Entity]:
    """Emit a QURAN_ENTITY per named-entity mention in a Qurʾān-genre span.

    Returns [] outside the configured Qurʾān genres. Delegates the fold, clitic,
    preceding-word rule, range-claiming, and offset anchoring to the shared
    gazetteer scan; each hit's payload carries its category and canonical name.
    """
    section: dict[str, Any] = config.raw.get(_CONFIG_SECTION, {})
    genres: frozenset[str] = frozenset(section.get("genres", []))
    if not genres or span.metadata.get(ENTITY__BOOK_TYPE_KEY) not in genres:
        return []
    _folded, hits = scan_gazetteer(span.text, _matchers(config))
    phase = PHASE_CONTRACTS["extract"].phase_number
    return [_entity(span, config, phase, start, end, payload) for start, end, _ms, payload in hits]


def _entity(
    span: Span, config: Config, phase: int, start: int, end: int, payload: tuple[str, str]
) -> Entity:
    """Anchor one QURAN_ENTITY to ``span.text[start:end]`` with its category and name."""
    category, name = payload
    metadata: dict[str, Any] = {ENTITY__CATEGORY_KEY: category, ENTITY__NAME_KEY: name}
    return create_entity(
        entity_type=QURAN__ENTITY_NAMED,
        text=span.text[start:end],
        char_start=start,
        char_end=end,
        span=span,
        extractor_id="quran_entity_extractor",
        config=config,
        phase=phase,
        metadata=metadata,
    )
