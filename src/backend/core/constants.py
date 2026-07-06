"""Named constants used across the backend.

Naming follows the ``DOMAIN__CONTEXT__THING`` pattern.

``READER__SOURCE_CACHE_MAX`` bounds the process-local cache of source-file
loads. Books are immutable, so the cap only limits memory when a session pages
through many books. ``CORPUS__SNIPPET_WINDOW_CHARS`` and
``CORPUS__SNIPPET_HEAD_CHARS`` set the excerpt geometry for the fold-aware
snippet built in ``repositories/corpus.py``: the characters kept on each side
of a match, and the head length shown on the guard path when the matched
window cannot be located. ``QURAN__SURAH_COUNT`` is the canonical chapter
count, the upper bound of every surah-number field; the ``CALENDAR__*``
bounds validate Hijri month/day references in the almanac.

``ARTIFACT__*`` names the build artifacts under ``data/``. Each filename is
the coupling point between the script that writes the artifact and the
repository that reads it, so it is declared once here and imported by both
sides. ``NARRATOR_LINK__*`` is the metadata contract between the writer
(``build/narrator_link.py`` stamps entity metadata) and the reader
(``repositories/manuscript.py`` resolves it back to registry ids); the key
and origin tokens live here so a rename cannot desynchronise the two sides.
``HADITH__ROLE_*`` is the closed ``role_in_context`` vocabulary shared the
same way: the pipeline's person emitter validates against it and the reader's
narrator projection filters on it, and repositories must never import
pipeline code, so the strings live here.
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
GRAMMAR__ENTITY_TERM: Final[str] = "GRAMMAR_TERM"
HADITH__ROLE_NARRATOR: Final[str] = "narrator"
HADITH__ROLE_RELATIVE_REF: Final[str] = "relative_reference"
HADITH__ROLE_MENTION: Final[str] = "mention"
SEARCH__PATTERN_CACHE_MAX: Final[int] = 512

CORPUS__SNIPPET_WINDOW_CHARS: Final[int] = 48
CORPUS__SNIPPET_HEAD_CHARS: Final[int] = 160
BUILD__COMMIT_EVERY: Final[int] = 400

QURAN__SURAH_COUNT: Final[int] = 114

CALENDAR__HIJRI_MONTHS: Final[int] = 12
CALENDAR__HIJRI_MONTH_DAY_MAX: Final[int] = 30

ARTIFACT__CORPUS_DB: Final[str] = "corpus.db"
ARTIFACT__MANUSCRIPT_DB: Final[str] = "manuscript.db"
ARTIFACT__REGISTRY_DB: Final[str] = "registry.db"
ARTIFACT__CITATIONS_DB: Final[str] = "citations.db"
ARTIFACT__BOOKS_INDEX: Final[str] = "books_index.json"

NARRATOR_LINK__METADATA_KEY: Final[str] = "narrator_link"
NARRATOR_LINK__ORIGIN_KEY: Final[str] = "origin"
NARRATOR_LINK__ID_KEY: Final[str] = "id"
NARRATOR_LINK__ORIGIN_RIJAL: Final[str] = "rijal"
NARRATOR_LINK__ORIGIN_CANONICAL: Final[str] = "canonical"
