"""Named-entity extractor for Qurʾānic text (Phase 3).

Where the narrator extractor models a hadith's chain and the grammar extractor
the vocabulary of naḥw, this extractor names the Qurʾān's own dramatis personae:
prophets, other persons, angels, peoples, places, revealed scriptures, and the
idols. It emits one QURAN_ENTITY per mention, categorized, so a later graph can
be built from the Qurʾān's own text — every verse that names موسى, every passage
that speaks of ثمود.

Matching is diacritic- and letter-variant-insensitive and clitic-aware: the
gazetteer name and the verse are both folded through ``fold_search``, an
attached conjunction/preposition (و ف ب ك ل) is allowed before the name, and a
trailing accusative alif is tolerated (نوحًا, هودًا). The match is mapped back to
the exact window of the name itself in the original pointed text — the leading
clitic is excluded from the entity — so the stored offsets bound the real name.

Several names coincide with a common word. Rather than a morphological guess
(CAMeL has no proper-noun reading for عاد or صالح at all), each such name carries
a deterministic preceding-word rule validated against every Qurʾānic occurrence:
``entity_prev`` keeps the name only after a listed word (صالح after أخاهم/يا/قوم;
العزيز after امرأت/أيها), and ``common_prev`` drops it after a listed word (عاد
after لا/من/حتى — the verb "returns" and adjective "transgressor"). A name with
neither rule is unambiguous and always kept.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Final

from backend.core.constants import ENTITY__CATEGORY_KEY, QURAN__ENTITY_NAMED
from backend.patterns import CompiledPattern, cached_compile, fold_search
from backend.pipeline.contracts import PHASE_CONTRACTS
from backend.pipeline.errors import ExtractError
from backend.pipeline.models import Entity, Span, create_entity

if TYPE_CHECKING:
    from backend.pipeline.config import Config

QURAN__NAME_KEY: Final[str] = "name"
QURAN__BOOK_TYPE_KEY: Final[str] = "book_type"

_CONFIG_SECTION: Final[str] = "quran_extraction"
_ENTITY_PREV_KEY: Final[str] = "entity_prev"
_COMMON_PREV_KEY: Final[str] = "common_prev"
_CONJUNCTION_CLITICS: Final[tuple[str, ...]] = ("و", "ف")

type _Rule = tuple[frozenset[str], frozenset[str]]
type _Matcher = tuple[str, str, CompiledPattern, _Rule]

_MATCHER_CACHE: dict[int, list[_Matcher]] = {}


def _name_regex(folded_name: str) -> CompiledPattern:
    """Match a folded name with an optional clitic prefix and accusative alif.

    Group 1 captures the name itself (plus a trailing accusative alif), so the
    entity anchors to the name and excludes any leading conjunction/preposition
    clitic (و ف ب ك ل). Boundaries forbid matching mid-word.
    """
    return cached_compile(rf"(?<![ء-ي])[وفبكل]?({re.escape(folded_name)}ا?)(?![ء-ي])")


def _matchers(config: Config) -> list[_Matcher]:
    """The compiled gazetteer for this config: (category, name, regex, rule).

    Built once per config from ``quran_extraction.gazetteer`` and cached. The
    rule is (entity_prev, common_prev) folded token sets; an empty pair means the
    name is unambiguous and always kept.
    """
    section: dict[str, Any] = config.raw.get(_CONFIG_SECTION, {})
    gazetteer: dict[str, list[dict[str, Any]]] = section.get("gazetteer", {})
    key = id(gazetteer)
    cached = _MATCHER_CACHE.get(key)
    if cached is not None:
        return cached
    built: list[_Matcher] = []
    for category, entries in gazetteer.items():
        for entry in entries:
            name = entry[QURAN__NAME_KEY]
            rule = (
                frozenset(fold_search(t) for t in entry.get(_ENTITY_PREV_KEY, [])),
                frozenset(fold_search(t) for t in entry.get(_COMMON_PREV_KEY, [])),
            )
            built.append((category, name, _name_regex(fold_search(name)), rule))
    built.sort(key=lambda m: -len(m[1]))
    _MATCHER_CACHE[key] = built
    return built


def _fold_with_offsets(text: str) -> tuple[str, list[int]]:
    """Fold ``text`` for search while recording each folded char's source index.

    ``fold_search`` folds character by character (drops marks, folds letter
    variants), so folding one char at a time reproduces it exactly and yields a
    folded→original index map. The returned list has one entry per folded char
    plus a trailing sentinel of ``len(text)``, so a folded span ``[fs, fe)`` maps
    to the original window ``[offsets[fs], offsets[fe])`` including any trailing
    diacritics on the last matched letter. Raises if the per-char fold and the
    bulk fold disagree, rather than emit a misaligned offset.
    """
    parts: list[str] = []
    offsets: list[int] = []
    for index, char in enumerate(text):
        for piece in fold_search(char):
            parts.append(piece)
            offsets.append(index)
    folded = "".join(parts)
    if folded != fold_search(text):
        raise ExtractError("fold_search is not character-local; offset map cannot be trusted")
    offsets.append(len(text))
    return folded, offsets


def _preceding_word(folded: str, match_start: int) -> str:
    """The folded word before ``match_start``, with a leading و/ف conjunction stripped."""
    before = folded[:match_start].split()
    if not before:
        return ""
    word = before[-1]
    if word[:1] in _CONJUNCTION_CLITICS:
        return word[1:]
    return word


def _rule_keeps(rule: _Rule, prev: str) -> bool:
    """Apply a name's preceding-word rule: whitelist keeps, blacklist drops, else keep."""
    entity_prev, common_prev = rule
    if entity_prev:
        return prev in entity_prev
    if common_prev:
        return prev not in common_prev
    return True


def quran_entity_extractor(span: Span, config: Config) -> list[Entity]:
    """Emit a QURAN_ENTITY per named-entity mention in a Qurʾān-genre span.

    Returns [] outside the configured Qurʾān genres. Scans the folded verse for
    every gazetteer name (longest first), claims character ranges so a shorter
    name never fires inside a longer one, applies each name's preceding-word rule
    to drop the common-word readings, and anchors each entity to the exact window
    of the name in the original pointed text.
    """
    section: dict[str, Any] = config.raw.get(_CONFIG_SECTION, {})
    genres: frozenset[str] = frozenset(section.get("genres", []))
    if not genres or span.metadata.get(QURAN__BOOK_TYPE_KEY) not in genres:
        return []
    folded, offsets = _fold_with_offsets(span.text)
    phase = PHASE_CONTRACTS["extract"].phase_number
    claimed: list[tuple[int, int]] = []
    found: list[tuple[int, int, str, str]] = []
    for category, name, regex, rule in _matchers(config):
        for match in regex.finditer(folded):
            start, end = offsets[match.start(1)], offsets[match.end(1)]
            if any(start < c_end and c_start < end for c_start, c_end in claimed):
                continue
            if not _rule_keeps(rule, _preceding_word(folded, match.start())):
                continue
            claimed.append((start, end))
            found.append((start, end, category, name))
    return [
        _entity(span, config, phase, start, end, category, name)
        for start, end, category, name in sorted(found)
    ]


def _entity(
    span: Span, config: Config, phase: int, start: int, end: int, category: str, name: str
) -> Entity:
    """Anchor one QURAN_ENTITY to ``span.text[start:end]`` with its category and name."""
    metadata: dict[str, Any] = {ENTITY__CATEGORY_KEY: category, QURAN__NAME_KEY: name}
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
