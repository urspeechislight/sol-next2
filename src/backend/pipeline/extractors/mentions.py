"""Person-mention extractor for matn text (Phase 3).

The narrator walk covers the isnad; this extractor covers the people the
hadith is ABOUT. It scans the matn region of a HADITH_TRANSMISSION span
(from the precomputed isnad_end) with three high-precision shapes:

* a nasab chain: one or more بن/ابن links (موسى بن جعفر);
* a kunya: أبو/أبي/أبا plus a name, optionally continuing into عبد الله-style
  compounds and a nasab tail (أبو حنيفة, أبو عبد الله);
* a titled word directly followed by an honorific ligature: the ال-prefixed
  title before a ﵇/﵈ salutation (الصادق ﵇). The ال requirement keeps speech
  verbs before honorifics (فقال ﵇) out.

Overlapping matches coalesce into their union before emission, so a kunya
running into a nasab yields one whole name instead of two fragments. Emitted
entities carry role ``mention``: they are not chain members, never receive a
chain position, and the reader's narrator projection excludes them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from backend.patterns import HONORIFIC_SIGNS, CompiledPattern, cached_compile
from backend.pipeline.models import Entity, Span
from backend.pipeline.name_extraction import clean_name_text
from backend.pipeline.persons import (
    NARRATOR__ROLE_MENTION,
    NARRATOR__SOURCE_MATN_PATTERN,
    PersonSpec,
    emit_person_entity,
)

if TYPE_CHECKING:
    from backend.pipeline.config import Config

_ARABIC_LETTERS: Final[str] = "ء-ي"
_NASAB_TAIL: Final[str] = rf"(?:\s+(?:بن|ابن)\s+[{_ARABIC_LETTERS}]+)"
_NASAB_MENTION_REGEX: CompiledPattern = cached_compile(rf"[{_ARABIC_LETTERS}]+{_NASAB_TAIL}+")
_KUNYA_MENTION_REGEX: CompiledPattern = cached_compile(
    rf"(?:أبو|أبي|أبا)\s+[{_ARABIC_LETTERS}]+(?:\s+الله)?{_NASAB_TAIL}*"
)
_TITLED_HONORIFIC_REGEX: CompiledPattern = cached_compile(
    rf"\bال[{_ARABIC_LETTERS}]+(?=\s*[{HONORIFIC_SIGNS}])"
)
_MENTION_REGEXES: Final[tuple[CompiledPattern, ...]] = (
    _NASAB_MENTION_REGEX,
    _KUNYA_MENTION_REGEX,
    _TITLED_HONORIFIC_REGEX,
)


def person_mention_extractor(span: Span, config: Config) -> list[Entity]:
    """Extract PERSON mentions from the matn region of a hadith span.

    Scans span.text from the precomputed isnad_end (the whole span when no
    chain was found there), coalesces overlapping pattern hits, and emits one
    ``mention`` entity per resulting name after the canonical name cleanup.
    """
    narrator_cfg = config.raw["narrator_extraction"]
    stopwords = frozenset(narrator_cfg.get("narrator_stopwords", []))
    max_chars = config.thresholds.narrator_name_max_chars
    matn_start = int(span.metadata.get("isnad_end", 0))
    windows: list[tuple[int, int]] = []
    for regex in _MENTION_REGEXES:
        windows.extend(match.span() for match in regex.finditer(span.text, matn_start))
    entities: list[Entity] = []
    for start, end in _coalesce(windows):
        name = clean_name_text(span.text[start:end])
        if not name or name in stopwords or len(name) > max_chars:
            continue
        entities.append(
            emit_person_entity(
                span=span,
                text=name,
                char_start=start,
                char_end=start + len(name),
                spec=PersonSpec(
                    role_in_context=NARRATOR__ROLE_MENTION,
                    source=NARRATOR__SOURCE_MATN_PATTERN,
                    config=config,
                    extractor_id="person_mention_extractor",
                ),
            )
        )
    return entities


def _coalesce(windows: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping [start, end) windows into their unions, in order.

    A kunya hit and a nasab hit over the same compound name (أبو عبد الله بن
    محمد) merge into the one full-name window instead of emitting fragments.
    """
    merged: list[tuple[int, int]] = []
    for start, end in sorted(windows):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
