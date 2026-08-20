"""Build layer: gather per-verse tafsir commentary candidates (Stage 1).

For each verse of a surah, search the five central Shia tafsir and hadith
sources (``QURAN__TAFSIR_SOURCES``) for the verse text and extract a bounded
commentary passage around each hit via the fold-aware passage locator in
``repositories.corpus``. Emits an intermediate candidates record consumed by
the Stage 2 LLM judge, which is not built here.

Mirrors the build-layer contract of ``catalog`` and ``corpus``: the per-verse
gathering logic lives here, the CLI shell lives in the driver script
``scripts/build_quran_tafsir.py``, and this module touches the filesystem only
through the repositories (the quran artifact, the corpus FTS index, and the
book source pages).
"""

from __future__ import annotations

from typing import Any, cast

from backend.core.constants import (
    ARTIFACT__QURAN_JSON,
    QURAN__TAFSIR_MAX_MATCHES_PER_SOURCE,
    QURAN__TAFSIR_PASSAGE_CHARS,
    QURAN__TAFSIR_SOURCES,
    TafsirSource,
)
from backend.core.logging import get_logger
from backend.models.search import CorpusMatch
from backend.repositories import corpus as corpus_repo
from backend.repositories import reader as reader_repo
from backend.repositories._data_loader import load_json

_logger = get_logger("shia-library.build.quran-tafsir")

_BASMALA_PREFACE_KEY = "0"


def _load_verses(surah: int) -> list[tuple[int, str]]:
    """Return ``[(ayah_number, verse_ar), ...]`` for ``surah`` in ascending
    ayah order, skipping the unnumbered basmala preface key ``"0"``. Verse text
    comes from ``data/quran.json`` at ``quran[str(surah)]["verses"][str(ayah)]
    ["ar"]``; a surah missing from the artifact raises ``ValueError`` rather
    than silently yielding an empty verse set."""
    doc_raw = load_json(ARTIFACT__QURAN_JSON)
    if not isinstance(doc_raw, dict):
        raise ValueError(f"{ARTIFACT__QURAN_JSON} is not a JSON object")
    doc = cast(dict[str, dict[str, Any]], doc_raw)
    surah_doc = doc.get(str(surah))
    if not isinstance(surah_doc, dict):
        raise ValueError(f"surah {surah} not found in {ARTIFACT__QURAN_JSON}")
    verses_raw = surah_doc.get("verses")
    if not isinstance(verses_raw, dict):
        raise ValueError(f"surah {surah} has no verses mapping")
    verses = cast(dict[str, dict[str, Any]], verses_raw)
    out: list[tuple[int, str]] = []
    for ayah_key, ayah_doc in verses.items():
        if ayah_key == _BASMALA_PREFACE_KEY or not ayah_key.isdigit():
            continue
        ar = ayah_doc.get("ar")
        if isinstance(ar, str) and ar.strip():
            out.append((int(ayah_key), ar))
    out.sort(key=lambda pair: pair[0])
    return out


def _best_matches(matches: list[CorpusMatch], cap: int) -> list[CorpusMatch]:
    """Return the ``cap`` highest-signal matches: shortest snippet first (the
    tightest fold around the verse), then earliest page. The verse text is the
    same for every match, so the shortest folded snippet marks the page that
    prints it most compactly and is kept ahead of looser hits."""
    ranked = sorted(matches, key=lambda m: (len(m.snippet), m.page))
    return ranked[:cap]


def _passage_for_match(match: CorpusMatch, verse_ar: str) -> str:
    """Extract the bounded commentary passage for one match from its page text.

    Loads the match's book source pages, finds the printed page, and slices a
    fold-aware window of ``QURAN__TAFSIR_PASSAGE_CHARS`` around the verse's
    folded location. Returns an empty string when the page is absent from the
    source, so the FTS index can reference a page the source file no longer
    carries without aborting the whole gather."""
    rows = reader_repo.page_rows(match.urn)
    page_text = next((r.content for r in rows if r.page == match.page), None)
    if not page_text:
        _logger.warning("tafsir-page-missing", urn=match.urn, page=match.page)
        return ""
    windows = corpus_repo.search_windows(verse_ar, "broad")
    _found, passage = corpus_repo.passage_around(
        page_text, windows, QURAN__TAFSIR_PASSAGE_CHARS
    )
    return passage


async def _candidates_for_verse(
    verse_ar: str, source: TafsirSource
) -> list[dict[str, Any]]:
    """Search one source for ``verse_ar`` and build capped candidate records,
    each carrying its urn, book, author, page, and the extracted passage.
    Matches whose urn does not start with the source prefix are dropped and
    logged: the book-title filter should already scope to the source, so a
    prefix mismatch signals catalog drift worth surfacing rather than keeping."""
    matches, _total = await corpus_repo.search(
        corpus_repo.SearchQuery(q=verse_ar, mode="broad", book=source.title)
    )
    best = _best_matches(matches, QURAN__TAFSIR_MAX_MATCHES_PER_SOURCE)
    out: list[dict[str, Any]] = []
    for match in best:
        if not match.urn.startswith(source.prefix):
            _logger.warning(
                "tafsir-source-prefix-mismatch", urn=match.urn, prefix=source.prefix
            )
            continue
        passage = _passage_for_match(match, verse_ar)
        out.append(
            {
                "urn": match.urn,
                "book": source.title,
                "author": source.author,
                "page": match.page,
                "passage_ar": passage,
            }
        )
    return out


async def gather_candidates(surah: int) -> dict[str, Any]:
    """Gather commentary candidates for every verse of ``surah`` across the five
    sources and return the intermediate Stage 1 record. Each verse entry carries
    its number, Arabic text, and the list of candidate passages; the driver
    writes this to the intermediate ``/tmp`` JSON for the Stage 2 judge."""
    verses = _load_verses(surah)
    results: list[dict[str, Any]] = []
    for ayah, verse_ar in verses:
        candidates: list[dict[str, Any]] = []
        for source in QURAN__TAFSIR_SOURCES:
            candidates.extend(await _candidates_for_verse(verse_ar, source))
        results.append(
            {
                "surah": surah,
                "ayah": ayah,
                "verse_ar": verse_ar,
                "candidates": candidates,
            }
        )
        _logger.info(
            "quran-tafsir-verse", surah=surah, ayah=ayah, candidates=len(candidates)
        )
    return {"surah": surah, "verses": results}
