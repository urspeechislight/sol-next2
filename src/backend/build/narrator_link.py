"""Build layer: link extracted narrator entities to the narrator registry.

The reader used to join narrator names to the registry in the browser,
downloading the first 600 of 284k rijal rows and fuzzy-matching client-side.
This module does that join once at build time against the FULL registry:
``NarratorLinker`` loads every rijal + person name from ``registry.db``,
indexes them by normalized first token, and ``link`` resolves one extracted
narrator name to its registry row. The match semantics mirror the frontend's
``narrators.ts`` exactly: names of at least two normalized tokens, matched
token-by-token from the start of the extracted name, allowing connective
tokens in the text that the registry name omits, longest registry name first,
the enriched person record winning over a raw rijal entry for the same
normalized name (the person carries the reconciled dates, reliability, stance,
and events the tarjama surfaces).

An unmatched name stays unlinked (``None``): a narrator the registry does not
know is shown as plain text, never linked to a wrong biography.
CENTRAL-005 permits the registry read SQL here.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from backend.core.constants import (
    ARTIFACT__REGISTRY_DB,
    HADITH__ENTITY_PERSON,
    HADITH__ROLE_RELATIVE_REF,
    NARRATOR_LINK__ID_KEY,
    NARRATOR_LINK__METADATA_KEY,
    NARRATOR_LINK__ORIGIN_KEY,
    NARRATOR_LINK__ORIGIN_PERSON,
    NARRATOR_LINK__ORIGIN_RIJAL,
)
from backend.patterns import normalize_arabic
from backend.pipeline.models import Manuscript
from backend.repositories._data_loader import open_ro_db

_MISSING_HINT: Final[str] = (
    "Narrator registry not built; run scripts/build_registry.py before linking"
)
_RIJAL_NAMES_QUERY: Final[str] = "SELECT id, full_name FROM rijal ORDER BY id"
_PERSON_NAMES_QUERY: Final[str] = (
    "SELECT person_id, full_name FROM person ORDER BY n_sources, person_id"
)
_MIN_NAME_TOKENS: Final[int] = 2

CONNECTIVE_TOKENS: Final[frozenset[str]] = frozenset(
    {"بن", "ابن", "بنت", "عن", "ابي", "ابو", "ال", "عبد", "حدثنا", "اخبرنا"}
)


@dataclass(frozen=True, slots=True)
class NarratorLink:
    """One resolved registry link: which registry and which row."""

    origin: str
    registry_id: int


@dataclass(frozen=True, slots=True)
class _Candidate:
    """One indexed registry name: its normalized tokens and its link."""

    tokens: tuple[str, ...]
    link: NarratorLink


class NarratorLinker:
    """Token-indexed lookup from extracted narrator names to registry rows."""

    def __init__(self, buckets: dict[str, list[_Candidate]]) -> None:
        self._buckets = buckets

    @classmethod
    def from_registry(cls) -> NarratorLinker:
        """Load every registry name and build the first-token index.

        Rijal entries index first and person entries overwrite them per
        normalized full name, so the enriched person record wins.
        """
        con = open_ro_db(ARTIFACT__REGISTRY_DB, _MISSING_HINT)
        pairs: list[tuple[str, str, int]] = []
        for query, origin in (
            (_RIJAL_NAMES_QUERY, NARRATOR_LINK__ORIGIN_RIJAL),
            (_PERSON_NAMES_QUERY, NARRATOR_LINK__ORIGIN_PERSON),
        ):
            pairs.extend((origin, str(row[1]), int(row[0])) for row in con.execute(query))
        return cls.from_names(pairs)

    @classmethod
    def from_names(cls, pairs: Iterable[tuple[str, str, int]]) -> NarratorLinker:
        """Build the index from ``(origin, full_name, registry_id)`` triples.

        Later triples overwrite earlier ones per normalized full name, so
        callers list rijal entries before person entries to make person win.
        Single-token names are dropped: too ambiguous to link safely.
        """
        by_name: dict[str, _Candidate] = {}
        for origin, full_name, registry_id in pairs:
            normalized = normalize_arabic(full_name)
            tokens = tuple(t for t in normalized.split(" ") if t)
            if len(tokens) < _MIN_NAME_TOKENS:
                continue
            by_name[normalized] = _Candidate(
                tokens=tokens, link=NarratorLink(origin=origin, registry_id=registry_id)
            )
        buckets: dict[str, list[_Candidate]] = {}
        for candidate in by_name.values():
            buckets.setdefault(candidate.tokens[0], []).append(candidate)
        for bucket in buckets.values():
            bucket.sort(key=lambda c: (-len(c.tokens), c.link.origin, c.link.registry_id))
        return cls(buckets)

    def link(self, name: str) -> NarratorLink | None:
        """Resolve one extracted narrator name to a registry link, or None.

        The registry name's tokens must match the extracted name's tokens in
        order from the start; connective tokens in the extracted name that
        the registry name omits are skipped (after the first token matched),
        exactly as the frontend matcher did.
        """
        name_tokens = [t for t in normalize_arabic(name).split(" ") if t]
        if not name_tokens:
            return None
        for candidate in self._buckets.get(name_tokens[0], []):
            if _matches(name_tokens, candidate.tokens):
                return candidate.link
        return None


def _matches(name_tokens: list[str], registry_tokens: tuple[str, ...]) -> bool:
    """Whether registry_tokens match name_tokens in order from the start."""
    ni = 0
    ri = 0
    while ri < len(registry_tokens) and ni < len(name_tokens):
        if name_tokens[ni] == registry_tokens[ri]:
            ni += 1
            ri += 1
            continue
        if ri > 0 and name_tokens[ni] in CONNECTIVE_TOKENS:
            ni += 1
            continue
        return False
    return ri == len(registry_tokens)


def annotate_manuscript(manuscript: Manuscript, linker: NarratorLinker) -> int:
    """Stamp each PERSON entity's metadata with its registry link; return links made.

    Walks every span's entities and adds ``narrator_link`` metadata
    (``{"origin": ..., "id": ...}``) where the linker resolves the name.
    Unresolved names get no key: absence means unlinked, never a guess.
    Relative-reference chain members (عن أبيه) carry no name to match and are
    skipped outright; linking the kinship word itself would be a wrong claim.
    """
    linked = 0
    for span in manuscript.spans:
        for entity in span.entities or []:
            if entity.entity_type != HADITH__ENTITY_PERSON:
                continue
            if entity.metadata.get("role_in_context") == HADITH__ROLE_RELATIVE_REF:
                continue
            link = linker.link(entity.text)
            if link is None:
                continue
            entity.metadata[NARRATOR_LINK__METADATA_KEY] = {
                NARRATOR_LINK__ORIGIN_KEY: link.origin,
                NARRATOR_LINK__ID_KEY: link.registry_id,
            }
            linked += 1
    return linked
