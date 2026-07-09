"""Build layer: materialize the Mizan al-I'tidal name registry artifact.

al-Dhahabi's *Mizan al-I'tidal fi Naqd al-Rijal* is a four-volume dictionary
of criticised hadith narrators whose ~9,900 biographies are numbered
continuously across the volumes. This module reads those volumes out of the
corpus full-text index (``data/corpus.db``), splits each numbered biography
into its own entry, and projects the opening name of each into the five
onomastic components (:mod:`backend.build.mizan_names`) so that narrators who
share a lineage are separable by kunya and nisba.

Segmentation is the load-bearing step. Entry numbers reset nowhere and climb
monotonically, but the raw text also carries footnote numbers, cross-reference
numbers, and year figures that match the ``N -`` shape. Rather than a
forward-tolerance filter (which cascades into mass rejection after one wide
gap), the true entry chain is recovered as the longest strictly-increasing
subsequence of the matched numbers, which locks onto the dense ``+1`` spine
and drops the stray numbers regardless of their position.

This is the WRITE side; the SQL DDL/INSERT here is permitted by CENTRAL-005
and the entry regex compiles through :func:`backend.patterns.cached_compile`
(CENTRAL-002). The artifact lifecycle (wipe, ``ANALYZE``, ``VACUUM``) lives in
:mod:`backend.build.runner`.
"""

from __future__ import annotations

import bisect
import json
import sqlite3
from pathlib import Path
from typing import Any

from backend.build import mizan_names
from backend.build import runner
from backend.core.constants import MIZAN__BOOK_TITLE, MIZAN__HEAD_WINDOW_CHARS
from backend.patterns import cached_compile

_ENTRY_RE = cached_compile(r"(?:^|[\s])(\d{1,5})\s*[-–]\s+(?!\d)")

SCHEMA: str = """
CREATE TABLE entry (
  entry_no INTEGER PRIMARY KEY,
  volume   INTEGER NOT NULL,
  page     INTEGER NOT NULL,
  name     TEXT NOT NULL DEFAULT '',
  ism      TEXT NOT NULL DEFAULT '',
  nasab    TEXT NOT NULL DEFAULT '[]',
  kunya    TEXT NOT NULL DEFAULT '',
  nisba    TEXT NOT NULL DEFAULT '[]',
  laqab    TEXT NOT NULL DEFAULT '[]',
  sigla    TEXT NOT NULL DEFAULT '[]',
  snippet  TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_entry_volume ON entry (volume);
CREATE INDEX idx_entry_ism ON entry (ism);
CREATE INDEX idx_entry_kunya ON entry (kunya);
"""

_INSERT = """
INSERT INTO entry
  (entry_no, volume, page, name, ism, nasab, kunya, nisba, laqab, sigla, snippet)
VALUES
  (:entry_no, :volume, :page, :name, :ism, :nasab, :kunya, :nisba, :laqab, :sigla, :snippet)
"""

TABLES: dict[str, str] = {"entry": _INSERT}


def _lis_indices(nums: list[int]) -> set[int]:
    """Return indices of a longest strictly-increasing subsequence of ``nums``."""
    tails: list[int] = []
    tails_idx: list[int] = []
    prev = [-1] * len(nums)
    for k, x in enumerate(nums):
        j = bisect.bisect_left(tails, x)
        if j == len(tails):
            tails.append(x)
            tails_idx.append(k)
        else:
            tails[j] = x
            tails_idx[j] = k
        prev[k] = tails_idx[j - 1] if j > 0 else -1
    chain: set[int] = set()
    k = tails_idx[-1] if tails_idx else -1
    while k != -1:
        chain.add(k)
        k = prev[k]
    return chain


def _volume_urns(con: sqlite3.Connection) -> list[tuple[str, int]]:
    """Return [(urn, volume), ...] for the Mizan volumes, ascending by volume."""
    rows = con.execute(
        "SELECT urn, volume FROM book WHERE title = ? ORDER BY volume",
        (MIZAN__BOOK_TITLE,),
    ).fetchall()
    return [(urn, int(vol)) for urn, vol in rows]


def _volume_stream(con: sqlite3.Connection, urn: str) -> tuple[str, list[int], list[int]]:
    """Return (text, offsets, pages) for one volume, pages joined by newlines."""
    rows = con.execute(
        "SELECT page, content FROM pages WHERE urn = ? ORDER BY page", (urn,)
    ).fetchall()
    parts: list[str] = []
    offsets: list[int] = []
    pages: list[int] = []
    cursor = 0
    for page, content in rows:
        offsets.append(cursor)
        pages.append(int(page))
        block = content + "\n"
        parts.append(block)
        cursor += len(block)
    return "".join(parts), offsets, pages


def iter_entries(con: sqlite3.Connection) -> list[tuple[int, int, int, str]]:
    """Return [(entry_no, volume, page, head_text), ...] for the whole book."""
    entries: list[tuple[int, int, int, str]] = []
    for urn, volume in _volume_urns(con):
        text, offsets, pages = _volume_stream(con, urn)
        matches = list(_ENTRY_RE.finditer(text))
        keep = _lis_indices([int(m.group(1)) for m in matches])
        for k, m in enumerate(matches):
            if k not in keep:
                continue
            start = m.end()
            end = matches[k + 1].start() if k + 1 < len(matches) else len(text)
            page = pages[bisect.bisect_right(offsets, m.start(1)) - 1]
            entries.append((int(m.group(1)), volume, page, text[start:end]))
    return entries


def entry_row(entry_no: int, volume: int, page: int, head_text: str) -> dict[str, Any]:
    """Project one segmented entry into an ``entry`` INSERT row."""
    window = head_text[:MIZAN__HEAD_WINDOW_CHARS]
    parsed = mizan_names.decompose(window)
    return {
        "entry_no": entry_no,
        "volume": volume,
        "page": page,
        "name": parsed["name"],
        "ism": parsed["ism"],
        "nasab": json.dumps(parsed["nasab"], ensure_ascii=False),
        "kunya": parsed["kunya"],
        "nisba": json.dumps(parsed["nisba"], ensure_ascii=False),
        "laqab": json.dumps(parsed["laqab"], ensure_ascii=False),
        "sigla": json.dumps(parsed["sigla"], ensure_ascii=False),
        "snippet": mizan_names.strip_markers(window)[0],
    }


def _export_json(rows: list[dict[str, Any]], json_out: Path) -> None:
    """Write the registry rows to ``json_out`` as a decoded JSON array."""
    payload = [
        {
            "entry_no": r["entry_no"],
            "volume": r["volume"],
            "page": r["page"],
            "name": r["name"],
            "ism": r["ism"],
            "nasab": json.loads(r["nasab"]),
            "kunya": r["kunya"],
            "nisba": json.loads(r["nisba"]),
            "laqab": json.loads(r["laqab"]),
            "sigla": json.loads(r["sigla"]),
        }
        for r in rows
    ]
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def build(source: Path, out: Path, json_out: Path) -> dict[str, int]:
    """Materialize the Mizan registry DB + JSON from ``source`` corpus.db."""
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    try:
        segmented = iter_entries(src)
    finally:
        src.close()
    rows = [entry_row(*seg) for seg in segmented]
    con = runner.create_artifact(out, SCHEMA)
    try:
        with con:
            con.executemany(_INSERT, rows)
        runner.finalize(con)
    finally:
        con.close()
    _export_json(rows, json_out)
    return {"entries": len(rows)}
