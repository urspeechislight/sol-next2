"""Compiled regex patterns — the CENTRAL-002 home for ``re`` use — plus the
Arabic text helpers built on them.

Two distinct fold capabilities live here, each with one definition:

* ``fold_search`` — the text-search SSOT. Strips diacritics + Quranic
  annotation signs and folds the alef/yaa/taa letter variants. The corpus FTS
  index stores text pre-folded with exactly this rule and the query is folded
  the same way, so a search matches regardless of hamza seat, alef-maqsura, or
  taa-marbuta spelling. The frontend mirrors it in ``lib/arabic.ts`` (foldSearch).
* ``normalize_arabic`` — the name/title fold used for fuzzy matching of
  narrator names and book titles, where whitespace is also collapsed.

Both share ``_fold_letters`` so the letter-folding rule exists once.
``strip_diacritics`` is display-only (verse bare form); it folds nothing.

The three mark classes are defined once here, side by side, so their
divergence is visible. ``ARABIC_MARKS`` covers the name-fold marks: the
harakat (fathatan through sukun), the superscript alef, and tatweel.
``SEARCH_MARKS`` is the wider display-only set stripped before search: the
Arabic signs (U+0610..U+061A), the harakat (U+064B..U+0652), the superscript
alef (U+0670), the Quranic sajdah/waqf/small-high annotation signs
(U+06D6..U+06ED), and tatweel (U+0640). It is a superset of ``ARABIC_MARKS``
so a pasted verse's waqf signs stay out of both the index and the query, and
it is codepoint-built so the class is unambiguous. ``TASHKEEL_MARKS`` is the
pipeline's TOC-title class (used by ``strip_tashkeel``), carried from
sol-next so TOC alignment folds titles exactly as the upstream extraction
did; it overlaps ``SEARCH_MARKS`` but is not equal to it, and unifying them
would change which TOC anchors match. Both combining-mark classes are
codepoint-built deliberately: a retyped literal of combining characters gets
silently reordered by bidi rendering, which corrupts the ranges.

``FOOTNOTE_MARKER`` is the one definition of the inline ``(N)`` footnote
reference shape; the pipeline's splitter, stripper, and tail regexes all
derive from it.

``HONORIFIC_SIGNS`` is the one definition of the Arabic honorific ligature
characters: the Quranic honorifics block (U+FD40..FD4F, the ﵇/﵈/﵉ salutations
printed after the Imams' names) and the ligature block carrying ﷺ and ﷿
(U+FDF0..FDFD). Codepoint-built for the same bidi reason as the mark classes.
Consumed by the pipeline's name cleaner (a trailing honorific is not part of
a narrator's name) and by the matn mention extractor (an honorific after a
titled word is a strong person signal).

``NAME_LEADING_PARTICLE`` is the one definition of the connective/preposition
particles (عن في من إلى على له به) that can prefix a name slice when a chain
connector or matn phrase is captured with the name; none of them begins an
Arabic personal name, so the name cleaner strips a run of them from the front.
على is written with alef maqsura (ى), so it matches only the preposition and
never the given name علي (ي).
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Final

from backend.core.constants import SEARCH__PATTERN_CACHE_MAX

type CompiledPattern = re.Pattern[str]

ARABIC_MARKS: Final[re.Pattern[str]] = re.compile("[ً-ْٰـ]")
_SEARCH_MARK_CPS: Final[tuple[int, ...]] = (
    *range(0x0610, 0x061B),
    *range(0x064B, 0x0653),
    0x0670,
    *range(0x06D6, 0x06EE),
    0x0640,
)
SEARCH_MARKS: Final[re.Pattern[str]] = re.compile(
    "[" + "".join(chr(c) for c in _SEARCH_MARK_CPS) + "]"
)
_TASHKEEL_CPS: Final[tuple[int, ...]] = (
    *range(0x0610, 0x061B),
    *range(0x064B, 0x0660),
    0x0670,
    *range(0x06D6, 0x06DD),
    *range(0x06DF, 0x06E5),
    0x06E7,
    0x06E8,
    *range(0x06EA, 0x06EE),
)
TASHKEEL_MARKS: Final[re.Pattern[str]] = re.compile(
    "[" + "".join(chr(c) for c in _TASHKEEL_CPS) + "]"
)
ARABIC_ALEF: Final[re.Pattern[str]] = re.compile("[أإآ]")
ARABIC_ALEF_MAQSURA: Final[re.Pattern[str]] = re.compile("ى")
ARABIC_TAA_MARBUTA: Final[re.Pattern[str]] = re.compile("ة")
WHITESPACE: Final[re.Pattern[str]] = re.compile(r"\s+")
FOOTNOTE_MARKER: Final[str] = r"\((\d+)\)"
_HONORIFIC_CPS: Final[tuple[int, ...]] = (
    *range(0xFD40, 0xFD50),
    *range(0xFDF0, 0xFDFE),
)
HONORIFIC_SIGNS: Final[str] = "".join(chr(c) for c in _HONORIFIC_CPS)
NAME_LEADING_PARTICLE: Final[re.Pattern[str]] = re.compile(r"^(?:(?:عن|في|من|إلى|على|له|به)\s+)+")


def _fold_letters(text: str) -> str:
    """Fold the alef variants, alef-maqsura, and taa-marbuta — the one
    letter-folding rule shared by ``fold_search`` and ``normalize_arabic``."""
    folded = ARABIC_ALEF.sub("ا", text)
    folded = ARABIC_ALEF_MAQSURA.sub("ي", folded)
    return ARABIC_TAA_MARBUTA.sub("ه", folded)


def fold_search(text: str) -> str:
    """Fold text for full-text search: drop diacritics + annotation signs and
    fold the alef/yaa/taa letter variants, preserving the surrounding structure.

    This is the single rule the corpus index is built with and that every query
    is folded by, so matching is insensitive to diacritics AND letter-variant
    spelling. It does NOT collapse whitespace — callers split on it as needed.
    """
    return _fold_letters(SEARCH_MARKS.sub("", text))


def normalize_arabic(text: str) -> str:
    """Fold a name/title for fuzzy comparison: drop harakat + tatweel, fold the
    alef/yaa/taa variants, then collapse whitespace. Used for narrator-name and
    book-title matching, not content search (see :func:`fold_search`)."""
    folded = _fold_letters(ARABIC_MARKS.sub("", text))
    return WHITESPACE.sub(" ", folded).strip()


def strip_diacritics(text: str) -> str:
    """Remove harakat + tatweel only, leaving the letters themselves intact.

    Unlike the folds above this changes no letters, so the result is still
    faithful Arabic to read on screen, just without vowel marks. Used to show a
    verse in both its pointed and bare forms.
    """
    return ARABIC_MARKS.sub("", text)


def strip_tashkeel(text: str) -> str:
    """Remove Arabic diacritics via the pipeline's TOC-title mark class.

    Used for diacritic-insensitive TOC title matching in the segment phase;
    see the module docstring for why this class stays distinct from
    ``ARABIC_MARKS`` and ``SEARCH_MARKS``.
    """
    return TASHKEEL_MARKS.sub("", text)


_HONORIFIC_INNER_MARKS: Final[str] = r"[ؐ-ًؚ-ٰٟۖ-ۭـ]*"
_HONORIFIC_PHRASES: Final[tuple[tuple[str, str], ...]] = (
    ("صلى الله عليه وآله وسلم", "﵌"),
    ("صلى الله عليه واله وسلم", "﵌"),
    ("صلى الله عليه وآله", "﵆"),
    ("صلى الله عليه واله", "﵆"),
    ("صلى الله عليه وسلم", "ﷺ"),
    ("عليه الصلاة والسلام", "﵊"),
    ("عليهما السلام", "﵉"),
    ("عليهم السلام", "﵈"),
    ("عليها السلام", "﵍"),
    ("عليه السلام", "﵇"),
    ("رضي الله تعالى عنهما", "﵄"),
    ("رضي الله عنهما", "﵄"),
    ("رضي الله تعالى عنهم", "﵃"),
    ("رضي الله عنهم", "﵃"),
    ("رضي الله تعالى عنهن", "﵅"),
    ("رضي الله عنهن", "﵅"),
    ("رضي الله تعالى عنها", "﵂"),
    ("رضي الله عنها", "﵂"),
    ("رضي الله تعالى عنه", "﵁"),
    ("رضي الله عنه", "﵁"),
    ("رحمهم الله", "﵏"),
    ("رحمه الله", "﵀"),
    ("تبارك وتعالى", "﵎"),
    ("جل جلاله", "ﷻ"),
    ("قدس سره", "﵋"),
)


def _tolerant_honorific(phrase: str) -> str:
    """A tashkeel-tolerant, letter-bounded regex for a spelled-out honorific phrase."""
    words = [
        _HONORIFIC_INNER_MARKS.join(re.escape(char) for char in word) + _HONORIFIC_INNER_MARKS
        for word in phrase.split()
    ]
    return r"(?<![ء-ي])" + r"\s+".join(words) + r"(?![ء-ي])"


_HONORIFIC_RE: Final[tuple[tuple[re.Pattern[str], str], ...]] = tuple(
    (re.compile(_tolerant_honorific(phrase)), ligature) for phrase, ligature in _HONORIFIC_PHRASES
)


def normalize_honorifics(text: str) -> str:
    """Replace spelled-out honorific phrases with their single ligature sign.

    ``صلى الله عليه وسلم`` -> ``ﷺ``, ``رضي الله عنه`` -> ``﵁``, ``عليه السلام`` ->
    ``﵇``, and so on, tashkeel and all (``صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ`` matches too).
    Standardizing to the ligature is what lets the whole pipeline treat honorifics
    one way: the name cleaner already cuts a name at the first ligature sign, so a
    spelled-out salutation no longer runs into a narrator's name. Phrases are
    ordered longest-first within a family so ``عنهما`` is not clipped to ``عنه``.
    """
    for regex, ligature in _HONORIFIC_RE:
        text = regex.sub(ligature, text)
    return text


@lru_cache(maxsize=SEARCH__PATTERN_CACHE_MAX)
def cached_compile(pattern: str, flags: int = 0) -> CompiledPattern:
    """Compile ``pattern`` once with ``flags``, cached per (pattern, flags).

    The single compile path for the ported pipeline's regexes. ``flags`` defaults
    to 0 (no flags) so util-local patterns compile exactly as in sol-next; config
    patterns are compiled with re.MULTILINE by compile_pattern_table. CENTRAL-002
    keeps every ``re.compile`` in this module.
    """
    return re.compile(pattern, flags)


def compile_pattern_table(
    raw_patterns: list[dict[str, str]],
) -> tuple[tuple[str, re.Pattern[str]], ...]:
    """Compile every ``{"id", "regex"}`` entry into an immutable
    ``(pattern_id, compiled)`` tuple, preserving config order.

    Raises ``ValueError`` naming the offending pattern when its regex fails to
    compile, so the pipeline config loader can surface it as a ConfigError at
    startup rather than running on a half-compiled pattern set.
    """
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for entry in raw_patterns:
        pattern_id = entry["id"]
        regex = entry["regex"]
        try:
            compiled.append((pattern_id, cached_compile(regex, re.MULTILINE)))
        except re.error as exc:
            raise ValueError(f"Pattern {pattern_id!r} has invalid regex: {exc}") from exc
    return tuple(compiled)


def escape_pattern(text: str) -> str:
    """Escape ``text`` for literal use in a regex (re.escape).

    The CENTRAL-002 home for re.escape so callers (e.g. the TOC title-to-regex
    builder) need not import re themselves.
    """
    return re.escape(text)


@lru_cache(maxsize=SEARCH__PATTERN_CACHE_MAX)
def cached_compile_alternation(
    parts: tuple[str, ...],
    joiner: str = "|",
    prefix: str = "",
    suffix: str = "",
    flags: int = 0,
) -> CompiledPattern:
    """Compile ``prefix + joiner.join(parts) + suffix`` once, cached per input.

    The shared builder for config word-list regexes (chain-continuation exclusions,
    transmission verbs, ...). Parts arrive pre-escaped; this joins and wraps them
    and compiles through cached_compile so the result is reused.
    """
    return cached_compile(prefix + joiner.join(parts) + suffix, flags)
