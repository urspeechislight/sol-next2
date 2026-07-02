"""Named constants used across the backend.

Naming follows the ``DOMAIN__CONTEXT__THING`` pattern.

``READER__SOURCE_CACHE_MAX`` bounds the process-local cache of source-file
loads. Books are immutable, so the cap only limits memory when a session pages
through many books. ``CORPUS__SNIPPET_WINDOW_CHARS`` and
``CORPUS__SNIPPET_HEAD_CHARS`` set the excerpt geometry for the fold-aware
snippet built in ``repositories/corpus.py``: the characters kept on each side
of a match, and the head length shown on the guard path when the matched
window cannot be located.
"""

from __future__ import annotations

from typing import Final

HTTP__DEFAULT_PAGE_SIZE: Final[int] = 24
HTTP__MAX_PAGE_SIZE: Final[int] = 200
HTTP__REQUEST_TIMEOUT_SECONDS: Final[int] = 30

READER__SOURCE_CACHE_MAX: Final[int] = 128

READER__SEARCH_DEFAULT_LIMIT: Final[int] = 30

BOOK__DEATH_YEAR_AH_MAX: Final[int] = 1500

HADITH__UNIT_ISNAD: Final[str] = "ISNAD_UNIT"
HADITH__UNIT_MATN: Final[str] = "MATN_UNIT"
HADITH__UNIT_HADITH: Final[str] = "HADITH_UNIT"
HADITH__ENTITY_PERSON: Final[str] = "PERSON"
SEARCH__PATTERN_CACHE_MAX: Final[int] = 512

CORPUS__SNIPPET_WINDOW_CHARS: Final[int] = 48
CORPUS__SNIPPET_HEAD_CHARS: Final[int] = 160
BUILD__COMMIT_EVERY: Final[int] = 400
