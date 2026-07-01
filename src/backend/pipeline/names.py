"""Shared person-name decomposition utilities.

The morphological building blocks for Arabic names (proclitic letters, hamza-alef
variants, patronymic connectors, compound-name prefixes) and the name-level
helpers built on them: clean_name_text (footnote-marker + trailing-punctuation
cleanup), build_sentence_start_re (editorial-prose disqualifier regex),
extract_kunya / extract_laqab (epithet extraction from span patterns), and
is_valid_person_name (the genealogy-or-kunya gate).

Ported from sol-next's src/utils/names.py. Every regex compiles through the
central backend.patterns module; the Arabic-morphology constants carry the
NARRATOR domain prefix because they exist only for narrator / person-name
decomposition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from backend.patterns import (
    CompiledPattern,
    cached_compile,
    cached_compile_alternation,
    escape_pattern,
)
from backend.pipeline.models import Pattern
from backend.pipeline.text import replace_footnote_markers

if TYPE_CHECKING:
    from backend.pipeline.config import Config

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


def extract_kunya(text: str, config: Config) -> tuple[str, int, int] | None:
    """Extract a kunya (أبو القاسم, أم حبيبة) from person-name text.

    Compiles the kunya pattern from config name_decomposition.kunya_pattern and
    searches the text for the first match.

    Returns the (kunya_text, start_offset, end_offset) of the match, or None when
    no kunya is present.
    """
    kunya_regex = cached_compile(config.raw["name_decomposition"]["kunya_pattern"])
    match = kunya_regex.search(text)
    if match is None:
        return None
    return (match.group(), match.start(), match.end())


def extract_laqab(
    span_text: str,
    span_patterns: list[Pattern],
    config: Config,
) -> tuple[str, int, int] | None:
    """Extract a laqab (epithet/nickname) from span text via LAQAB_MARKER patterns.

    Finds the first LAQAB_MARKER in span_patterns, then scans span_text from the
    marker's end to the first boundary character (comma, newline, paren, digit)
    or the next DEATH_MARKER/BIRTH_MARKER position, skipping leading whitespace.

    Returns the (laqab_text, start_offset, end_offset), or None when there is no
    LAQAB_MARKER or the scan yields empty text.
    """
    laqab_markers = sorted(
        (pattern for pattern in span_patterns if pattern.pattern_id == "LAQAB_MARKER"),
        key=lambda pattern: pattern.char_start,
    )
    if not laqab_markers:
        return None

    marker = laqab_markers[0]
    laqab_start = marker.char_end
    while laqab_start < len(span_text) and span_text[laqab_start] in " \t":
        laqab_start += 1
    if laqab_start >= len(span_text):
        return None

    boundary_regex = cached_compile(config.raw["name_decomposition"]["laqab_boundaries"])
    laqab_end = len(span_text)
    boundary_match = boundary_regex.search(span_text, laqab_start)
    if boundary_match is not None:
        laqab_end = min(laqab_end, boundary_match.start())
    for pattern in span_patterns:
        ends_laqab = (
            pattern.pattern_id in ("DEATH_MARKER", "BIRTH_MARKER")
            and pattern.char_start > laqab_start
        )
        if ends_laqab:
            laqab_end = min(laqab_end, pattern.char_start)

    laqab_text = clean_name_text(span_text[laqab_start:laqab_end])
    if not laqab_text:
        return None
    return (laqab_text, laqab_start, laqab_end)


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
