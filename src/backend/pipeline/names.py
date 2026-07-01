"""Shared person-name decomposition utilities.

The morphological building blocks for Arabic names (proclitic letters, hamza-alef
variants, patronymic connectors, compound-name prefixes) and the name-level
helpers built on them: clean_name_text (footnote-marker + trailing-punctuation
cleanup), build_sentence_start_re (editorial-prose disqualifier regex), and
is_valid_person_name (the genealogy-or-kunya gate). The kunya/laqab epithet
extractors left with the name_decomposition config section; they return with
the biography/rijal extractors that consume them.

Ported from sol-next's src/utils/names.py. Every regex compiles through the
central backend.patterns module; the Arabic-morphology constants carry the
NARRATOR domain prefix because they exist only for narrator / person-name
decomposition.
"""

from __future__ import annotations

from typing import Final

from backend.patterns import (
    CompiledPattern,
    cached_compile,
    cached_compile_alternation,
    escape_pattern,
)
from backend.pipeline.text import replace_footnote_markers

NARRATOR__CLITIC_CHARS: Final[frozenset[str]] = frozenset({"و", "ف", "ل", "ك", "ب", "س"})
NARRATOR__HAMZA_ALEF_CHARS: Final[frozenset[str]] = frozenset({"أ", "إ", "آ", "ا", "ء"})
NARRATOR__PATRONYMIC_CONNECTORS: Final[frozenset[str]] = frozenset({"بن", "ابن"})
NARRATOR__COMPOUND_NAME_PREFIXES: Final[frozenset[str]] = frozenset(
    {"عبد", "عبيد", "أبو", "أبي", "أبا", "أم", "أمّ", "أمة"}
)

_NAME_TRAILING_PUNCT_REGEX: CompiledPattern = cached_compile(r"[\s،,:.]+$")


def clean_name_text(name: str) -> str:
    """Remove footnote markers (replaced with spaces) and trailing punctuation.

    Inline footnote references like (2) sit between name tokens; replacing them
    with a space keeps the tokens separated, then the trailing Arabic/Latin
    delimiters (، , : .) that are structural rather than part of the name are
    stripped.
    """
    cleaned = replace_footnote_markers(name)
    cleaned = _NAME_TRAILING_PUNCT_REGEX.sub("", cleaned)
    return cleaned.strip()


def build_sentence_start_re(disqualifiers: tuple[str, ...]) -> CompiledPattern:
    """Build the sentence-start disqualifier regex from config.

    Names beginning with these words (قد, أما, كما, ...) are editorial prose,
    not person names; the rijal and biography extractors reject them. Compiled
    through the central pattern cache so identical disqualifier sets share one
    compiled object across extractor invocations.
    """
    return cached_compile_alternation(
        tuple(escape_pattern(word) for word in disqualifiers),
        prefix=r"^(?:",
        suffix=r")\b",
    )


def is_valid_person_name(
    name: str,
    sentence_start_regex: CompiledPattern,
    genealogy_regex: CompiledPattern,
    kunya_start_regex: CompiledPattern,
) -> bool:
    """Return whether the cleaned text is actually a person name.

    A valid name either contains a genealogy marker (بن, ابن, بنت) signalling a
    nasab chain, or starts with a kunya (أبو, أبي, أم). Editorial prose, book
    references, and numbered commentary paragraphs are rejected.
    """
    if not name:
        return False
    if sentence_start_regex.match(name):
        return False
    if genealogy_regex.search(name):
        return True
    return bool(kunya_start_regex.match(name))
