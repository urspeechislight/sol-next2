"""Historical-event extractor for narrative genres (Phase 3).

Names the historical events a sīra / tārīkh / rijāl text recounts: the Prophet's
battles (بدر, أحد, خيبر, حنين), the early fitnas (الجمل, صفين, النهروان), the
conquests (فتح مكة, القادسية), and the martyrdoms (كربلاء). It emits one EVENT
entity per mention carrying the canonical event id and its type (BATTLE,
CONQUEST, CIVIL_STRIFE, …), so a later graph can be built on the shared
historical spine — every passage that speaks of صفين, every biography that
places its subject at بدر.

Matching runs through the shared ``gazetteer_match`` scan. Event names that also
read as a common word (بدر "full moon", أحد "one", الجمل "the camel") carry a
preceding-word rule — the same precision-first mechanism the Qurʾān names use —
so a bare common word is not mistaken for the battle.

When a participation marker (شهد "witnessed", استشهد "was martyred at") sits in
the words just before the event, the entity records the ``role`` and the
triggering ``indicator``; the participant is a co-located PERSON entity, so the
person→event edge is derived at graph time rather than guessed here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from backend.core.constants import (
    ARABIC__CONJUNCTION_CLITICS as _CONJUNCTION_CLITICS,
)
from backend.core.constants import (
    ENTITY__NAME_KEY,
    EVENT__ENTITY_NAMED,
)
from backend.patterns import fold_search
from backend.pipeline.contracts import PHASE_CONTRACTS
from backend.pipeline.gazetteer_match import Matcher, ScanHit, matchers_for_span, scan_gazetteer
from backend.pipeline.models import Entity, Span, create_entity

if TYPE_CHECKING:
    from backend.pipeline.config import Config

EVENT__TYPE_KEY: Final[str] = "event_type"
EVENT__ID_KEY: Final[str] = "event_id"
EVENT__ROLE_KEY: Final[str] = "role"
EVENT__INDICATOR_KEY: Final[str] = "indicator"

_CONFIG_SECTION: Final[str] = "event_extraction"
_PARTICIPATION_KEY: Final[str] = "participation"
_PARTICIPATION_WINDOW: Final[int] = 4

type _Payload = tuple[str, str, str]

_MATCHER_CACHE: dict[int, list[Matcher[_Payload]]] = {}
_ROLE_CACHE: dict[int, dict[str, str]] = {}


def _role_markers(config: Config) -> dict[str, str]:
    """Folded participation-marker word -> role, from config, cached."""
    participation: dict[str, list[str]] = config.raw.get(_CONFIG_SECTION, {}).get(
        _PARTICIPATION_KEY, {}
    )
    key = id(participation)
    if key not in _ROLE_CACHE:
        _ROLE_CACHE[key] = {
            fold_search(word): role for role, words in participation.items() for word in words
        }
    return _ROLE_CACHE[key]


def _participation(folded: str, match_start: int, roles: dict[str, str]) -> tuple[str, str] | None:
    """The (role, indicator) if a participation marker sits in the preceding window."""
    window = folded[:match_start].split()[-_PARTICIPATION_WINDOW:]
    for word in reversed(window):
        stripped = word[1:] if word[:1] in _CONJUNCTION_CLITICS else word
        role = roles.get(stripped)
        if role is not None:
            return role, word
    return None


def _entity(
    span: Span,
    config: Config,
    phase: int,
    folded: str,
    roles: dict[str, str],
    hit: ScanHit[_Payload],
) -> Entity:
    """Anchor one EVENT to its slice with its type, id, and any participation role."""
    start, end, match_start, (event_type, event_id, name) = hit
    metadata: dict[str, Any] = {
        ENTITY__NAME_KEY: name,
        EVENT__TYPE_KEY: event_type,
        EVENT__ID_KEY: event_id,
    }
    participation = _participation(folded, match_start, roles)
    if participation is not None:
        metadata[EVENT__ROLE_KEY], metadata[EVENT__INDICATOR_KEY] = participation
    return create_entity(
        entity_type=EVENT__ENTITY_NAMED,
        text=span.text[start:end],
        char_start=start,
        char_end=end,
        span=span,
        extractor_id="event_extractor",
        config=config,
        phase=phase,
        metadata=metadata,
    )


def event_extractor(span: Span, config: Config) -> list[Entity]:
    """Emit an EVENT entity per historical-event mention in a narrative-genre span.

    Returns [] outside the configured genres. Delegates the fold, clitic,
    preceding-word rule, range-claiming, and offset anchoring to the shared
    gazetteer scan, then stamps each event's type, id, and any participation role.
    """
    matchers = matchers_for_span(
        span,
        config,
        _CONFIG_SECTION,
        _MATCHER_CACHE,
        lambda etype, entry: (etype, entry[EVENT__ID_KEY], entry[ENTITY__NAME_KEY]),
    )
    if matchers is None:
        return []
    folded, hits = scan_gazetteer(span.text, matchers)
    roles = _role_markers(config)
    phase = PHASE_CONTRACTS["extract"].phase_number
    return [_entity(span, config, phase, folded, roles, hit) for hit in hits]
