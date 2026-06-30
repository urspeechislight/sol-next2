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

# ---------- Corpus full-text search --------------------------------------------

# Excerpt geometry for the fold-aware snippet built in repositories/corpus.py:
# characters kept on each side of a match, and the head length shown when the
# matched window cannot be located (it always can, this is the guard path).
CORPUS__SNIPPET_WINDOW_CHARS: Final[int] = 48
CORPUS__SNIPPET_HEAD_CHARS: Final[int] = 160
CORPUS__BUILD_COMMIT_EVERY: Final[int] = 400
