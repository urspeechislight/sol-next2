"""Shared Arabic gazetteer-matching for Phase 3 extractors.

The Qurʾān named-entity extractor and the historical-event extractor both match
a curated, categorised gazetteer against fully-pointed Arabic verse/prose. The
shape is identical: fold away diacritics and letter variants, tolerate an
attached conjunction/preposition clitic and a trailing accusative alif, anchor
each hit to the exact window of the name in the original text, claim ranges so a
shorter name never fires inside a longer one, and drop the common-word reading
of an ambiguous name by a preceding-word rule. Only the payload differs — a
category for the Qurʾān, an event type and id for events — so ``compile_matchers``
and ``scan_gazetteer`` are generic over it and the two extractors share one
implementation.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final

from backend.core.constants import (
    ARABIC__CONJUNCTION_CLITICS as _CONJUNCTION_CLITICS,
)
from backend.core.constants import (
    ENTITY__BOOK_TYPE_KEY,
    ENTITY__NAME_KEY,
)
from backend.patterns import CompiledPattern, cached_compile, fold_search, fold_with_offsets
from backend.pipeline.models import Span

if TYPE_CHECKING:
    from backend.pipeline.config import Config

ENTITY_PREV_KEY: Final[str] = "entity_prev"
COMMON_PREV_KEY: Final[str] = "common_prev"

type Matcher[T] = tuple[str, CompiledPattern, frozenset[str], frozenset[str], T]
type ScanHit[T] = tuple[int, int, int, T]


def _name_regex(folded_name: str) -> CompiledPattern:
    """Match a folded name with an optional clitic prefix and accusative alif.

    Group 1 captures the name itself (plus a trailing accusative alif), so a hit
    anchors to the name and excludes any leading conjunction/preposition clitic
    (و ف ب ك ل). Boundaries forbid mid-word hits.
    """
    return cached_compile(rf"(?<![ء-ي])[وفبكل]?({re.escape(folded_name)}ا?)(?![ء-ي])")


def preceding_word(folded: str, match_start: int) -> str:
    """The folded word immediately before ``match_start`` (empty at text start)."""
    before = folded[:match_start].split()
    return before[-1] if before else ""


def _rule_keeps(entity_prev: frozenset[str], common_prev: frozenset[str], prev: str) -> bool:
    """Apply a name's preceding-word rule: whitelist keeps, blacklist drops, else keep.

    The preceding word is tested with and without a leading و/ف clitic, so a rule
    token like ``وقعة`` (whose و is a root letter) matches ``وقعة`` while a genuine
    conjunction ``وبدر`` still matches the base word ``بدر``.
    """
    prev_stripped = prev[1:] if prev[:1] in _CONJUNCTION_CLITICS else prev
    forms = {prev, prev_stripped}
    if entity_prev:
        return bool(forms & entity_prev)
    if common_prev:
        return not (forms & common_prev)
    return True


def compile_matchers[T](
    gazetteer: dict[str, list[dict[str, Any]]], payload: Callable[[str, dict[str, Any]], T]
) -> list[Matcher[T]]:
    """Compile a categorised gazetteer into matchers, longest name first.

    ``payload(category, entry)`` produces whatever the extractor stamps on its
    entity. Each entry supplies a ``name`` and optional ``entity_prev`` /
    ``common_prev`` preceding-word rules.
    """
    built: list[Matcher[T]] = []
    for category, entries in gazetteer.items():
        for entry in entries:
            name = entry[ENTITY__NAME_KEY]
            entity_prev = frozenset(fold_search(token) for token in entry.get(ENTITY_PREV_KEY, []))
            common_prev = frozenset(fold_search(token) for token in entry.get(COMMON_PREV_KEY, []))
            built.append(
                (
                    name,
                    _name_regex(fold_search(name)),
                    entity_prev,
                    common_prev,
                    payload(category, entry),
                )
            )
    built.sort(key=lambda matcher: -len(matcher[0]))
    return built


def cached_matchers[T](
    cache: dict[int, list[Matcher[T]]],
    gazetteer: dict[str, list[dict[str, Any]]],
    payload: Callable[[str, dict[str, Any]], T],
) -> list[Matcher[T]]:
    """Compile ``gazetteer`` into matchers once, memoized in ``cache`` by the
    gazetteer's identity.

    A parsed Config is held for the process lifetime and each extractor's
    gazetteer is a distinct sub-dict, so ``id(gazetteer)`` is a stable per-config
    key and the compile runs once. The one compile-once path every gazetteer
    extractor shares; the caller owns the typed ``cache`` so each keeps its payload
    type.
    """
    key = id(gazetteer)
    if key not in cache:
        cache[key] = compile_matchers(gazetteer, payload)
    return cache[key]


def in_configured_genres(span: Span, section: dict[str, Any]) -> bool:
    """Whether ``span``'s book type is one of the genres ``section`` configures.

    A gazetteer extractor emits nothing outside its configured genres; this is the
    one definition of that gate, shared by the Qurʾān and event extractors.
    """
    genres = frozenset(section.get("genres", []))
    return bool(genres) and span.metadata.get(ENTITY__BOOK_TYPE_KEY) in genres


def matchers_for_span[T](
    span: Span,
    config: Config,
    section_name: str,
    cache: dict[int, list[Matcher[T]]],
    payload: Callable[[str, dict[str, Any]], T],
) -> list[Matcher[T]] | None:
    """The compiled gazetteer matchers to scan ``span`` with, or ``None`` when the
    span's book type is outside the genres ``section_name`` configures.

    The one entry point a gazetteer extractor needs: it applies the genre gate and
    returns the cached, compiled matchers, so the extractor body reduces to scan +
    stamp. ``payload(category, entry)`` builds whatever the extractor puts on its
    entities; ``cache`` is that extractor's own typed matcher cache.
    """
    section: dict[str, Any] = config.raw.get(section_name, {})
    if not in_configured_genres(span, section):
        return None
    return cached_matchers(cache, section.get("gazetteer", {}), payload)


def scan_gazetteer[T](text: str, matchers: list[Matcher[T]]) -> tuple[str, list[ScanHit[T]]]:
    """Scan ``text`` for every matcher, claiming ranges and applying the rules.

    Returns the folded text and, for each kept match, ``(start, end, match_start,
    payload)`` — the entity window in the original text, the folded index of the
    full match (for a caller that reads more preceding context, e.g.
    participation), and the payload — sorted by position.
    """
    folded, offsets = fold_with_offsets(text)
    claimed: list[tuple[int, int]] = []
    hits: list[ScanHit[T]] = []
    for _name, regex, entity_prev, common_prev, payload in matchers:
        for match in regex.finditer(folded):
            start, end = offsets[match.start(1)], offsets[match.end(1)]
            if any(
                start < claimed_end and claimed_start < end
                for claimed_start, claimed_end in claimed
            ):
                continue
            if not _rule_keeps(entity_prev, common_prev, preceding_word(folded, match.start())):
                continue
            claimed.append((start, end))
            hits.append((start, end, match.start(), payload))
    return folded, sorted(hits, key=lambda hit: (hit[0], hit[1]))
