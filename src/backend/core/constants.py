"""Named constants used across the backend.

Naming follows the ``DOMAIN__CONTEXT__THING`` pattern.
"""

from __future__ import annotations

from typing import Final

# ---------- HTTP / API ---------------------------------------------------------

HTTP__DEFAULT_PAGE_SIZE: Final[int] = 24
HTTP__MAX_PAGE_SIZE: Final[int] = 200
HTTP__REQUEST_TIMEOUT_SECONDS: Final[int] = 30

# ---------- Database -----------------------------------------------------------

DATABASE__POOL_SIZE: Final[int] = 5
DATABASE__POOL_TIMEOUT_SECONDS: Final[int] = 10

# ---------- Cache --------------------------------------------------------------

CACHE__DAILY_TTL_SECONDS: Final[int] = 86400  # 24 hours

# ---------- Reader content -----------------------------------------------------

# Process-local cache for source-file loads. Books are immutable; the cap
# bounds memory if a session pages through many books.
READER__SOURCE_CACHE_MAX: Final[int] = 128

# ---------- Reader in-book search ----------------------------------------------

READER__SEARCH_DEFAULT_LIMIT: Final[int] = 30

BOOK__DEATH_YEAR_AH_MAX: Final[int] = 1500

HADITH__UNIT_ISNAD: Final[str] = "ISNAD_UNIT"
HADITH__UNIT_MATN: Final[str] = "MATN_UNIT"
HADITH__UNIT_HEADING: Final[str] = "HEADING_UNIT"
HADITH__UNIT_FOOTNOTE: Final[str] = "FOOTNOTE_UNIT"
HADITH__UNIT_BASMALA: Final[str] = "BASMALA_UNIT"
HADITH__UNIT_TYPES_WITH_TEXT: Final[frozenset[str]] = frozenset(
    {
        HADITH__UNIT_ISNAD,
        HADITH__UNIT_MATN,
        HADITH__UNIT_HEADING,
        HADITH__UNIT_FOOTNOTE,
        HADITH__UNIT_BASMALA,
    }
)
HADITH__UNIT_HADITH: Final[str] = "HADITH_UNIT"
HADITH__UNIT_ID_FORMAT: Final[str] = "{manifestation_id}_u{index:04d}"
HADITH__ENTITY_ID_FORMAT: Final[str] = "{span_id}_e{index:02d}"
HADITH__BEHAVIOR_TRANSMISSION: Final[str] = "HADITH_TRANSMISSION"
HADITH__BEHAVIOR_GENERAL_PROSE: Final[str] = "GENERAL_PROSE"
HADITH__BEHAVIOR_SECTION_HEADING: Final[str] = "SECTION_HEADING"
HADITH__BEHAVIOR_EDITORIAL_FRONTMATTER: Final[str] = "EDITORIAL_FRONTMATTER"
HADITH__SPAN_TYPE_PARAGRAPH: Final[str] = "paragraph"
HADITH__ENTITY_PERSON: Final[str] = "PERSON"
HADITH__PATTERN_HEADING_MARKER: Final[str] = "HEADING_MARKER"
HADITH__PATTERN_ATTRIBUTION: Final[str] = "ATTRIBUTION"
HADITH__PATTERN_MATN_BOUNDARY_HINT: Final[str] = "MATN_BOUNDARY_HINT"
HADITH__PATTERN_SPEECH_VERB_GENERIC: Final[str] = "SPEECH_VERB_GENERIC"
HADITH__STRATEGY_WHOLE_SPAN: Final[str] = "whole_span"
HADITH__STRATEGY_SANAD_MATN: Final[str] = "sanad_matn_split"
HADITH__MAX_NARRATOR_RANK: Final[int] = 12
HADITH__SUBSECTION_HEADING_MAX_CHARS: Final[int] = 200
SEARCH__PATTERN_CACHE_MAX: Final[int] = 512

# ---------- Corpus full-text search --------------------------------------------

# Excerpt geometry for the fold-aware snippet built in repositories/corpus.py:
# characters kept on each side of a match, and the head length shown when the
# matched window cannot be located (it always can, this is the guard path).
CORPUS__SNIPPET_WINDOW_CHARS: Final[int] = 48
CORPUS__SNIPPET_HEAD_CHARS: Final[int] = 160
CORPUS__BUILD_COMMIT_EVERY: Final[int] = 400
