"""Repository for the Daily editorial: date-rotated picks from ``data/daily.json``.

The data file holds parallel pools (verses, hadiths, books); each pool rotates
independently by calendar day, so adding one entry to any pool immediately
lengthens that pool's cycle without touching the others. Selection is the day's
ordinal modulo the pool size: deterministic across restarts and replicas, no
stored state. The day boundary is UTC, stated rather than inherited from the
server's locale.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from backend.models.daily import Daily, DailyPool, Verse, VersePick
from backend.repositories import quran as quran_repo
from backend.repositories._data_loader import load_json


def _pick(pool_size: int, on: date) -> int:
    """The pool index for a calendar day: stable, cycles the whole pool."""
    return on.toordinal() % pool_size


def _verse(pick: VersePick) -> Verse:
    """Compose the served verse: canonical text plus the pool's curation.

    The pool stores only the surah:ayah reference and the tafsir excerpts;
    the scripture text has exactly one source, the Qurʾān repository, so the
    daily verse can never drift from the text the reader serves.
    """
    ayah = quran_repo.get_verse(pick.surah_n, pick.ayah_n)
    return Verse(
        surah_n=pick.surah_n,
        ayah_n=pick.ayah_n,
        ayah_ar=ayah.text_ar,
        ayah_en=ayah.text_en,
        tafsirs=pick.tafsirs,
    )


def for_day(on: date) -> Daily:
    """The Daily selection for ``on``: one entry from each pool."""
    pool = DailyPool.model_validate(load_json("daily.json"))
    return Daily(
        verse=_verse(pool.verses[_pick(len(pool.verses), on)]),
        hadith=pool.hadiths[_pick(len(pool.hadiths), on)],
        book=pool.books[_pick(len(pool.books), on)],
    )


def get_today() -> Daily:
    """Return the Daily selection for the current UTC date."""
    return for_day(datetime.now(tz=UTC).date())
