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
``HADITH__FOOTNOTE_MARKER_MAX_GAP`` bounds the footnote-entry sequential-
plausibility guard in ``pipeline/text.py::split_footnote_block``, used by
both the pipeline and the reader; see docs/councils/
2026-07-03-reader-footnotes-council.md for why it exists.
"""

from __future__ import annotations

from typing import Final, NamedTuple

HADITH__FOOTNOTE_MARKER_MAX_GAP: Final[int] = 50

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
QURAN__ENTITY_NAMED: Final[str] = "QURAN_ENTITY"
EVENT__ENTITY_NAMED: Final[str] = "EVENT"
DATE__ENTITY_HIJRI_YEAR: Final[str] = "HIJRI_YEAR"
DATE__ENTITY_LUNAR_MONTH: Final[str] = "LUNAR_MONTH"
QURAN__MANIFESTATION_ID: Final[str] = "quran"
QURAN__TITLE_AR: Final[str] = "القرآن الكريم"
QURAN__TITLE_EN: Final[str] = "The Noble Qurʾān"
ENTITY__CATEGORY_KEY: Final[str] = "category"
ENTITY__NAME_KEY: Final[str] = "name"
ENTITY__BOOK_TYPE_KEY: Final[str] = "book_type"
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

ARABIC__DEFINITE_ARTICLE: Final[str] = "ال"
ARABIC__CONJUNCTION_CLITICS: Final[tuple[str, ...]] = ("و", "ف")

MANUSCRIPT__INDEX_MISSING_HINT: Final[str] = (
    "Manuscript index not built; run scripts/build_manuscript_index.py to materialize it"
)

ARTIFACT__MANUSCRIPT_DB: Final[str] = "manuscript.db"
ARTIFACT__REGISTRY_DB: Final[str] = "registry.db"
ARTIFACT__CITATIONS_DB: Final[str] = "citations.db"
ARTIFACT__BOOKS_INDEX: Final[str] = "books_index.json"
ARTIFACT__TOC_INDEX: Final[str] = "toc_index.json"
ARTIFACT__TOC_OVERRIDES: Final[str] = "toc_overrides.json"

TOC_SYNTH__LETTER_MIN: Final[int] = 3
TOC_SYNTH__NUMBERED_MIN: Final[int] = 10
TOC_SYNTH__NUMBERED_MIN_PAGES: Final[int] = 8
TOC_SYNTH__NUMBERED_MIN_SPAN: Final[float] = 0.2
TOC_SYNTH__TITLE_MAX_CHARS: Final[int] = 40
TOC_SYNTH__SCRAPED_SPARSE_MAX: Final[int] = 2
TOC_SYNTH__MIN_CONTENT_PAGES: Final[int] = 20

NARRATOR_LINK__METADATA_KEY: Final[str] = "narrator_link"
NARRATOR_LINK__ORIGIN_KEY: Final[str] = "origin"
NARRATOR_LINK__ID_KEY: Final[str] = "id"
NARRATOR_LINK__ORIGIN_RIJAL: Final[str] = "rijal"
NARRATOR_LINK__ORIGIN_PERSON: Final[str] = "person"


class TafsirSource(NamedTuple):
    """One tafsir or hadith source mined for per-verse commentary candidates.

    The five Shia tafsir and hadith works whose pages are scanned for each
    verse text. ``prefix`` is the URN stem shared by every volume of the work
    (used to confirm a hit belongs to its source); ``title`` is the Arabic book
    title used as the corpus book filter; ``author`` is the romanized author
    carried into the candidates record.
    """

    prefix: str
    title: str
    author: str


ARTIFACT__QURAN_JSON: Final[str] = "quran.json"
ARTIFACT__QURAN_TAFSIR_JSON: Final[str] = "quran_tafsir.json"
QURAN__TAFSIR_PASSAGE_CHARS: Final[int] = 1500
QURAN__TAFSIR_MAX_MATCHES_PER_SOURCE: Final[int] = 3
QURAN__TAFSIR_SOURCES: Final[tuple[TafsirSource, ...]] = (
    TafsirSource("sImRzyMh", "تفسير القمي", "Ali Ibn Ibrahim Al-Qummi"),
    TafsirSource("wt1u7Yp0", "تفسير العياشي", "Muhammad Ibn Masud Al-Ayyashi"),
    TafsirSource(
        "vr7Zr2wC",
        "تفسير كنز الدقائق وبحر الغرائب",
        "Al-Shaykh Muhammad Ibn Muhammad Rida Al-Qummi Al-Mashhadi",
    ),
    TafsirSource("B4x1RjeV", "البرهان في تفسير القرآن", "Al-Sayyid Hashim Al-Bahrani"),
    TafsirSource("iz32WsFJ", "بحار الأنوار", "Al-Allamah Al-Majlisi"),
)
