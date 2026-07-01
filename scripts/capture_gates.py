"""Capture and compare regression-gate baselines for the rebuild stages.

Three artifacts per run, written to ``~/sol-next2-rebuild-gates/`` and
suffixed with the label given as argv[1] (``baseline``, ``stage2``, ...):

  ``openapi-<label>.json``     the FastAPI schema, keys sorted
  ``golden-<label>.json``      responses from representative endpoints
  ``manuscript-<label>.json``  per-table schema, row count, and content hash

The manuscript stats come from ``sqlite3.Connection.iterdump`` so this file
authors no SQL; hashes are order-independent (sorted INSERT lines), which
makes two artifacts comparable even if a rebuild inserts rows in a different
order. ``GOLD_HADITH_URN``/``GOLD_HADITH_PAGE`` anchor the one reader page
currently served from extracted hadith units (found once from the baseline
artifact); if a refactor changes what that page returns, the golden diff is
the gate doing its job.

Usage, from the repo root so pydantic-settings finds ``.env``:

    uv run python scripts/capture_gates.py baseline
    uv run python scripts/capture_gates.py stage2
    diff <(python -m json.tool ~/sol-next2-rebuild-gates/golden-baseline.json) \
         <(python -m json.tool ~/sol-next2-rebuild-gates/golden-stage2.json)
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app

GATES_DIR = Path.home() / "sol-next2-rebuild-gates"
MANUSCRIPT_DB = Path(__file__).resolve().parent.parent / "data" / "manuscript.db"
QUERY = "الحمد"
GOLD_HADITH_URN = "mEbWpeQ5_02"
GOLD_HADITH_PAGE = 433
_EXPECTED_ARGC = 2

_INSERT_LINE = re.compile(r'^INSERT INTO "(\w+)"')
_CREATE_LINE = re.compile(r'^CREATE TABLE "?(\w+)"?')


def capture_manuscript() -> dict[str, dict[str, object]]:
    """Per-table schema line, row count, and sorted-content sha256 via iterdump."""
    con = sqlite3.connect(f"file:{MANUSCRIPT_DB}?mode=ro", uri=True)
    inserts: dict[str, list[str]] = defaultdict(list)
    schemas: dict[str, str] = {}
    for line in con.iterdump():
        insert_match = _INSERT_LINE.match(line)
        if insert_match:
            inserts[insert_match.group(1)].append(line)
            continue
        create_match = _CREATE_LINE.match(line)
        if create_match:
            schemas[create_match.group(1)] = line
    con.close()
    stats: dict[str, dict[str, object]] = {}
    for table, schema_line in sorted(schemas.items()):
        digest = hashlib.sha256()
        for line in sorted(inserts[table]):
            digest.update(line.encode())
        stats[table] = {
            "schema": schema_line,
            "count": len(inserts[table]),
            "sha256": digest.hexdigest(),
        }
    return stats


def capture_golden(client: TestClient) -> dict[str, object]:
    """Fetch every representative endpoint once and record status + body."""
    books = client.get("/api/books", params={"limit": 3}).json()
    urn = books["items"][0]["urn"]
    calls: list[tuple[str, str, dict[str, str | int]]] = [
        ("books_list", "/api/books", {"limit": 3}),
        ("book_get", f"/api/books/{urn}", {}),
        ("book_toc", f"/api/books/{urn}/toc", {}),
        ("book_page_1", f"/api/books/{urn}/pages/1", {}),
        ("hadith_page", f"/api/books/{GOLD_HADITH_URN}/pages/{GOLD_HADITH_PAGE}", {}),
        ("book_search", f"/api/books/{urn}/search", {"q": QUERY, "limit": 3}),
        ("domains", "/api/domains", {}),
        ("daily", "/api/daily", {}),
        ("works", "/api/works", {"limit": 3}),
        ("search", "/api/search", {"q": QUERY, "limit": 3}),
        ("search_facets", "/api/search/facets", {"q": QUERY}),
        ("search_books", "/api/search/books", {"q": QUERY, "limit": 3}),
        ("quran_search", "/api/quran/search", {"q": QUERY, "limit": 3}),
        ("quran_verse", "/api/quran/1/1", {}),
        ("rijal", "/api/rijal", {"limit": 3}),
        ("canonical", "/api/canonical", {"limit": 3}),
        ("missing_book_404", "/api/books/urn:does-not-exist", {}),
    ]
    golden: dict[str, object] = {}
    for name, path, params in calls:
        resp = client.get(path, params=params)
        golden[name] = {"status": resp.status_code, "body": resp.json()}
    return golden


def main() -> None:
    """Write the three gate artifacts for the label in argv[1]."""
    if len(sys.argv) != _EXPECTED_ARGC:
        raise SystemExit("usage: capture_gates.py <label>")
    label = sys.argv[1]
    GATES_DIR.mkdir(exist_ok=True)
    client = TestClient(app)
    openapi_path = GATES_DIR / f"openapi-{label}.json"
    openapi_path.write_text(json.dumps(app.openapi(), indent=1, sort_keys=True))
    golden_path = GATES_DIR / f"golden-{label}.json"
    golden_path.write_text(
        json.dumps(capture_golden(client), indent=1, sort_keys=True, ensure_ascii=False)
    )
    manuscript_path = GATES_DIR / f"manuscript-{label}.json"
    manuscript_path.write_text(json.dumps(capture_manuscript(), indent=1, sort_keys=True))
    print(f"gates written: {openapi_path} {golden_path} {manuscript_path}")


if __name__ == "__main__":
    main()
