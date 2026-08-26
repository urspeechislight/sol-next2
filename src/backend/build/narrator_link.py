"""Build layer: link extracted narrator entities to the narrator registry.

The reader used to join narrator names to the registry in the browser,
downloading a sample of registry rows and fuzzy-matching client-side. This
module does that join once at build time against the FULL registry:
``NarratorLinker`` loads every alias from ``registry.db``'s ``narrator_alias``
table, indexes them by normalized first token, and ``link`` resolves one
extracted narrator name to its registry row. The match semantics mirror the
frontend's retired ``narrators.ts`` matcher: names of at least two normalized
tokens, matched token-by-token from the start of the extracted name, allowing
connective tokens in the text that the registry name omits, longest registry
name first, the primary alias winning over kunya/nisba variants of the same
normalized name.

An unmatched name stays unlinked (``None``): a narrator the registry does not
know is shown as plain text, never linked to a wrong biography.
CENTRAL-005 permits the registry read SQL here.
"""

from __future__ import annotations

import json
import sqlite3
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
    NARRATOR_LINK__ORIGIN_NARRATOR,
)
from backend.patterns import normalize_narrator_name
from backend.pipeline.models import Manuscript
from backend.repositories._data_loader import open_ro_db

_MISSING_HINT: Final[str] = (
    "Narrator registry not built; run scripts/build_registry.py before linking"
)
_ALIAS_NAMES_QUERY: Final[str] = (
    "SELECT a.narrator_id, a.name_normalized, a.name_role FROM narrator_alias a"
)
_MIN_NAME_TOKENS: Final[int] = 2
_ROLE_PRECEDENCE: Final[dict[str, int]] = {"primary": 3, "variant": 2, "kunya": 1, "nisba": 0}

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
        """Load every alias and build the first-token index.

        Aliases are stored ``name_normalized`` with the sol-next3 fold
        (diacritics stripped, letter variants folded, ابن collapsed to بن),
        which is what the match semantics below already assume — the tokens
        are split directly from the stored value.
        """
        con = open_ro_db(ARTIFACT__REGISTRY_DB, _MISSING_HINT)
        pairs = [
            (str(row["name_normalized"]), str(row["name_role"] or "") or None, int(row["narrator_id"]))
            for row in con.execute(_ALIAS_NAMES_QUERY)
        ]
        return cls.from_names(pairs)

    @classmethod
    def from_names(
        cls, pairs: Iterable[tuple[str, str | None, int]]
    ) -> NarratorLinker:
        """Build the index from ``(name_normalized, name_role, narrator_id)`` triples.

        Names are folded through the registry fold (idempotent on stored
        ``name_normalized`` values) so raw spellings index the same way.
        Triples are sorted so that, for the same normalized name, the most
        role-precedent alias (primary > variant > kunya > nisba > unknown)
        and then the lowest narrator id is written last and wins. Single-token
        names are dropped: too ambiguous to link safely.
        """
        by_name: dict[str, _Candidate] = {}
        for name, _role_name, narrator_id in sorted(
            pairs, key=lambda p: (_role_rank(p[1]), -p[2])
        ):
            normalized = normalize_narrator_name(name)
            tokens = tuple(t for t in normalized.split(" ") if t)
            if len(tokens) < _MIN_NAME_TOKENS:
                continue
            by_name[normalized] = _Candidate(
                tokens=tokens,
                link=NarratorLink(
                    origin=NARRATOR_LINK__ORIGIN_NARRATOR, registry_id=narrator_id
                ),
            )
        buckets: dict[str, list[_Candidate]] = {}
        for candidate in by_name.values():
            buckets.setdefault(candidate.tokens[0], []).append(candidate)
        for bucket in buckets.values():
            bucket.sort(key=lambda c: (-len(c.tokens), c.link.registry_id))
        return cls(buckets)

    def link(self, name: str) -> NarratorLink | None:
        """Resolve one extracted narrator name to a registry link, or None.

        The registry name's tokens must match the extracted name's tokens in
        order from the start; connective tokens in the extracted name that
        the registry name omits are skipped (after the first token matched),
        exactly as the frontend matcher did.
        """
        name_tokens = [t for t in normalize_narrator_name(name).split(" ") if t]
        if not name_tokens:
            return None
        for candidate in self._buckets.get(name_tokens[0], []):
            if _matches(name_tokens, candidate.tokens):
                return candidate.link
        return None


def _role_rank(role: str | None) -> int:
    """Sort rank of a name_role: higher wins (primary > variant > kunya > nisba > unknown)."""
    return _ROLE_PRECEDENCE.get(str(role or ""), len(_ROLE_PRECEDENCE))


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
    (``{"origin": "narrator", "id": ...}``) where the linker resolves the name.
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


_RESTAMP_SELECT: Final[str] = (
    "SELECT rowid, text_ar, metadata FROM entity "
    "WHERE entity_type = :person_type "
    "AND json_extract(metadata, '$.role_in_context') <> :relative"
)
_RESTAMP_UPDATE: Final[str] = "UPDATE entity SET metadata = :metadata WHERE rowid = :rowid"


def restamp(con: sqlite3.Connection, linker: NarratorLinker | None = None) -> int:
    """Re-link narrator metadata on an EXISTING manuscript.db entity table in place.

    One UPDATE pass over the PERSON entities: each row's metadata JSON is
    re-resolved through the current registry (stale ``narrator_link`` keys are
    dropped, fresh ones stamped), everything else in the metadata is preserved
    as-is. Returns the number of entities now linked. The caller owns the
    connection (and its commit), so this composes with any build script shell.
    """
    if linker is None:
        linker = NarratorLinker.from_registry()
    linked = 0
    updates: list[tuple[str, int]] = []
    for row in con.execute(_RESTAMP_SELECT, {"person_type": HADITH__ENTITY_PERSON, "relative": HADITH__ROLE_RELATIVE_REF}):
        metadata: dict[str, object] = json.loads(row["metadata"])
        metadata.pop(NARRATOR_LINK__METADATA_KEY, None)
        link = linker.link(str(row["text_ar"]))
        if link is not None:
            metadata[NARRATOR_LINK__METADATA_KEY] = {
                NARRATOR_LINK__ORIGIN_KEY: link.origin,
                NARRATOR_LINK__ID_KEY: link.registry_id,
            }
            linked += 1
        updates.append((json.dumps(metadata, ensure_ascii=False), int(row["rowid"])))
    con.executemany(_RESTAMP_UPDATE, updates)
    return linked
