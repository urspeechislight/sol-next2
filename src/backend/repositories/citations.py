"""Read-only repository for the Qur'an citation sidecar (``data/citations.db``).

The sidecar is a structured layer OVER the byte-identical corpus: one row per
citation, anchored by ``(urn, page, char_offset, char_len)`` back into the
immutable source, carrying its resolved ``(surah, aya_start, aya_end)``, tier,
and verse-match verdict. It is built read-only by
``~/sol-quran-citation-audit-20260703/build_sidecar.py`` (a corpus pass that
never writes the source); see that run's README for the classification + verse
matching. This repository serves only the auto-linkable set to the reader: the
clean tier whose adjacent quote was confirmed to be the cited verse (``exact``,
``short``, or ``neighbor`` match). The ambiguous tail and the mismatch review
queue are held in the sidecar but not served as confident links. Opened
read-only + immutable via the shared artifact opener (CENTRAL-005 keeps all SQL
here).
"""

from __future__ import annotations

import sqlite3
from typing import Final

from backend.core.constants import ARTIFACT__CITATIONS_DB
from backend.models.citation import Citation
from backend.repositories._data_loader import open_ro_db

_PAGE_SQL: Final[str] = (
    "SELECT char_offset, char_len, surah, aya_start, aya_end, verse_match "
    "FROM citation "
    "WHERE urn = ? AND page = ? "
    "AND tier = 'clean' AND verse_match IN ('exact', 'short', 'neighbor') "
    "ORDER BY char_offset"
)
_VERSE_COUNT_SQL: Final[str] = (
    "SELECT count(DISTINCT urn) FROM citation WHERE surah = ? AND aya_start = ?"
)


def _connect() -> sqlite3.Connection:
    """Open the citation sidecar read-only via the shared artifact opener."""
    return open_ro_db(
        ARTIFACT__CITATIONS_DB,
        "Citation sidecar not built; run build_sidecar.py to materialize it",
    )


def page_citations(urn: str, page: int) -> list[Citation]:
    """Auto-linkable Qur'an citations on one page, ordered by their position.

    A page with no verified citations (or an unknown URN) returns ``[]``: an
    empty apparatus is a legitimate result, not an error.
    """
    rows = _connect().execute(_PAGE_SQL, (urn, page)).fetchall()
    return [
        Citation(
            offset=r["char_offset"],
            length=r["char_len"],
            surah=r["surah"],
            aya_start=r["aya_start"],
            aya_end=r["aya_end"],
            verse_match=r["verse_match"],
        )
        for r in rows
    ]


def books_citing(surah: int, aya: int) -> int:
    """How many distinct books cite ``surah:aya`` (reverse-concordance count)."""
    row = _connect().execute(_VERSE_COUNT_SQL, (surah, aya)).fetchone()
    return int(row[0]) if row else 0
