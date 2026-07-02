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
from backend.models.quran import Ayah
from backend.patterns import WHITESPACE, fold_search, strip_diacritics
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


@lru_cache(maxsize=1)
def _folded_index() -> tuple[tuple[int, int, int, str, str, str | None], ...]:
    """Every numbered ayah as ``(surah, ayah, verse_count, text_ar, folded_ar,
    text_en)``, folded once with the search SSOT so a term scan is a substring
    test. The prefatory basmala (key ``0``) is skipped: it is not a numbered ayah."""
    rows: list[tuple[int, int, int, str, str, str | None]] = []
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
            folded = WHITESPACE.sub(" ", fold_search(text_ar)).strip()
            rows.append((surah, ayah, verse_count, text_ar, folded, verse.get("en")))
    return tuple(rows)


def search_verses(q: str, limit: int, offset: int) -> tuple[list[Ayah], int]:
    """Find every ayah whose folded text contains the folded query, in surah:ayah
    order, returning the ``(slice, total)`` the route wraps in a Page. A blank
    query matches nothing rather than every verse."""
    needle = WHITESPACE.sub(" ", fold_search(q)).strip()
    if not needle:
        return [], 0
    hits = [
        _make_ayah(surah, ayah, verse_count, text_ar, text_en)
        for surah, ayah, verse_count, text_ar, folded, text_en in _folded_index()
        if needle in folded
    ]
    return slice_page(hits, limit, offset)
