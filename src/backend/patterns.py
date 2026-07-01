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
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Final

from backend.core.constants import SEARCH__PATTERN_CACHE_MAX

type CompiledPattern = re.Pattern[str]

# Harakat (fathatan..sukun), superscript alef, and tatweel — the name-fold marks.
ARABIC_MARKS: Final[re.Pattern[str]] = re.compile("[ً-ْٰـ]")
# Every display-only mark stripped before SEARCH: arabic signs (0610-061A),
# harakat (064B-0652), superscript alef (0670), Quranic annotation signs —
# sajdah/waqf/small-high marks (06D6-06ED), and tatweel (0640). Superset of
# ARABIC_MARKS; the wider set keeps a pasted verse's waqf signs out of the index
# and query. Codepoint-built so the class is unambiguous.
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
ARABIC_ALEF: Final[re.Pattern[str]] = re.compile("[أإآ]")
ARABIC_ALEF_MAQSURA: Final[re.Pattern[str]] = re.compile("ى")
ARABIC_TAA_MARBUTA: Final[re.Pattern[str]] = re.compile("ة")
WHITESPACE: Final[re.Pattern[str]] = re.compile(r"\s+")


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
