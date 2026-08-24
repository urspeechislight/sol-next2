"""Read-only Qurʾān verse lookup over the curated ``data/quran.json`` artifact.

The JSON is keyed by surah number; each surah carries a ``verses`` map
(ayah number -> {ar, en}, with the prefatory basmala stored at key ``0``) and
a canonical ``verse_count``. ``get_verse`` resolves a surah:ayah reference to
an :class:`Ayah`, raising ``ResourceNotFoundError`` when the surah or ayah is
out of range so the API answers a clean 404 rather than an empty verse.

``search_verses`` scans the same artifact for an Arabic term: it folds the query
and every verse with the search SSOT (``fold_search``) and returns the ayat whose
text contains it, so a reader can find a word, not only a surah:ayah reference.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, cast

from backend.core.errors import ResourceNotFoundError
from backend.models.quran import Ayah, Surah
from backend.patterns import WHITESPACE, fold_search, strip_diacritics
from backend.query_language import parse_query
from backend.repositories._data_loader import load_json, slice_page

_FILE = "quran.json"


def _quran() -> dict[str, Any]:
    return load_json(_FILE)


def get_verse(surah: int, ayah: int) -> Ayah:
    """Resolve a surah:ayah reference to its verse text (both pointed + bare)."""
    chapter = _quran().get(str(surah))
    if not isinstance(chapter, dict):
        raise ResourceNotFoundError(kind="surah", identifier=str(surah))
    chapter_dict = cast(dict[str, Any], chapter)
    verses = chapter_dict.get("verses")
    if not isinstance(verses, dict):
        raise ResourceNotFoundError(kind="surah", identifier=str(surah))
    verses_dict = cast(dict[str, Any], verses)
    verse = verses_dict.get(str(ayah))
    if not isinstance(verse, dict):
        raise ResourceNotFoundError(kind="ayah", identifier=f"{surah}:{ayah}")
    verse_dict = cast(dict[str, Any], verse)
    return _make_ayah(
        surah, ayah, chapter_dict["verse_count"], verse_dict["ar"], verse_dict.get("en")
    )


def get_surah(surah: int) -> Surah:
    """Resolve a surah number to its full run of numbered ayat, in order.

    The prefatory basmala (key ``0``) is skipped, matching the search index:
    it is not a numbered ayah.
    """
    chapter = _quran().get(str(surah))
    if not isinstance(chapter, dict):
        raise ResourceNotFoundError(kind="surah", identifier=str(surah))
    chapter_dict = cast(dict[str, Any], chapter)
    verses = cast(dict[str, Any], chapter_dict["verses"])
    verse_count = cast(int, chapter_dict["verse_count"])
    ayat = [
        _make_ayah(surah, n, verse_count, verses[str(n)]["ar"], verses[str(n)].get("en"))
        for n in sorted(int(a) for a in verses)
        if n != 0
    ]
    return Surah(surah=surah, verse_count=verse_count, verses=ayat)


def _make_ayah(surah: int, ayah: int, verse_count: int, text_ar: str, text_en: str | None) -> Ayah:
    """Assemble an :class:`Ayah`, deriving the bare ``text_plain`` from ``text_ar``."""
    return Ayah(
        surah=surah,
        ayah=ayah,
        verse_count=verse_count,
        text_ar=text_ar,
        text_plain=strip_diacritics(text_ar),
        text_en=text_en,
    )


def _search_fold(text: str) -> str:
    """The one searchable form of Qurʾān text: diacritic-folded via the search
    SSOT with whitespace collapsed. Index build and query MUST fold identically
    or every search silently misses, so both call this."""
    return WHITESPACE.sub(" ", fold_search(text)).strip()


@lru_cache(maxsize=1)
def _folded_index() -> tuple[tuple[int, int, int, str, str, str | None, str], ...]:
    """Every numbered ayah as ``(surah, ayah, verse_count, text_ar, folded_ar,
    text_en, folded_en)``, folded once with the search SSOT so a term scan is a
    substring test. The prefatory basmala (key ``0``) is skipped: it is not a
    numbered ayah. folded_en is the casefolded English translation, the only
    English text the corpus currently serves, so Quran search matches both
    languages."""
    rows: list[tuple[int, int, int, str, str, str | None, str]] = []
    quran = _quran()
    for surah in sorted(int(s) for s in quran):
        chapter = quran[str(surah)]
        verses = chapter["verses"]
        verse_count = chapter["verse_count"]
        for ayah in sorted(int(a) for a in verses):
            if ayah == 0:
                continue
            verse = verses[str(ayah)]
            text_ar = verse["ar"]
            folded = _search_fold(text_ar)
            text_en = verse.get("en")
            folded_en = _fold_en(text_en) if text_en else ""
            rows.append((surah, ayah, verse_count, text_ar, folded, text_en, folded_en))
    return tuple(rows)


def _fold_en(text: str) -> str:
    """The searchable form of English text: casefolded, whitespace-collapsed —
    the English counterpart of _search_fold, so query and index fold identically."""
    return " ".join(text.casefold().split())


def _clause_matches(clause: str, folded_ar: str, folded_en: str) -> bool:
    """True when a phrase clause appears in the folded Arabic or folded
    English form of the verse."""
    needle_ar = _search_fold(clause)
    if needle_ar and needle_ar in folded_ar:
        return True
    needle_en = _fold_en(clause)
    return bool(needle_en) and needle_en in folded_en


def search_verses(q: str, limit: int, offset: int) -> tuple[list[Ayah], int]:
    """Find every ayah whose text contains the query, in surah:ayah order,
    returning the ``(slice, total)`` the route wraps in a Page. Matching covers
    both the folded Arabic and the folded English translation (the only English
    text in the corpus). Boolean syntax (``+`` / ``NOT``, the shared query
    language) requires every include clause and rejects any exclude clause; a
    blank query matches nothing rather than every verse."""
    parsed = parse_query(q)
    if parsed is not None:
        hits = [
            _make_ayah(surah, ayah, verse_count, text_ar, text_en)
            for surah, ayah, verse_count, text_ar, folded, text_en, folded_en in _folded_index()
            if all(_clause_matches(c, folded, folded_en) for c in parsed.includes)
            and not any(_clause_matches(c, folded, folded_en) for c in parsed.excludes)
        ]
        return slice_page(hits, limit, offset)
    hits = [
        _make_ayah(surah, ayah, verse_count, text_ar, text_en)
        for surah, ayah, verse_count, text_ar, folded, text_en, folded_en in _folded_index()
        if _clause_matches(q, folded, folded_en)
    ]
    return slice_page(hits, limit, offset)
