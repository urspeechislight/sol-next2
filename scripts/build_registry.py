#!/usr/bin/env python3
"""Build the read-only narrator registry SQLite artifact (ADR-0001).

Reads sol-next's pipeline-produced corpus JSON (read-only; never writes into
the sol-next tree) and projects only the served fields into a compact SQLite
database under sol-next2's ``data/``. The backend opens this artifact
read-only and serves ``/api/rijal`` + ``/api/canonical`` from it with
near-zero resident memory, instead of holding ~900 MB of JSON in RAM.

All SQL lives in ``backend.repositories.registry``; this script only shapes
data (the project layout permits regex + one-off projection in ``scripts/``).
Pass 1 covers rijal + canonical; the 3.3 GB history corpus is a later pass.

Run (on buildhost)::

    uv run python scripts/build_registry.py
    uv run python scripts/build_registry.py --corpus /path/corpus.json --out data/registry.db
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any, Final

from backend.core.paths import data_path
from backend.repositories import registry

_SOLNEXT_RIJAL: Final[Path] = Path.home() / "code" / "sol-next" / "data" / "rijal"
_DEFAULT_CORPUS: Final[Path] = _SOLNEXT_RIJAL / "corpus.json"
_DEFAULT_CANONICAL: Final[Path] = _SOLNEXT_RIJAL / "canonical.json"
_DEFAULT_OUT: Final[Path] = data_path("registry.db")

# Quality-classification thresholds, mirrored from sol-next config/sol.yaml
# (thresholds.rijal_classify_{isnad,long}_min_chars) so the served `category`
# matches the upstream reader's filter semantics exactly.
_ISNAD_MIN_CHARS: Final[int] = 60
_LONG_MIN_CHARS: Final[int] = 80

_REF_RE: Final[re.Pattern[str]] = re.compile(r"\[\s*\d+\s*:\s*\d+|ح\s+\d{3,}")
_ISNAD_RE: Final[re.Pattern[str]] = re.compile(r"(?:روى عن|سمع|حدث)")
_ABBREV_RE: Final[re.Pattern[str]] = re.compile(r"^[دمسعق]\s+\(")
_NUMBERED_RE: Final[re.Pattern[str]] = re.compile(r"^\d{3,}")


def _classify(name: str) -> str:
    """Classify a rijal entry by data quality, mirroring sol-next's rules."""
    if _REF_RE.search(name):
        return "ref_number"
    if _ISNAD_RE.search(name) and len(name) > _ISNAD_MIN_CHARS:
        return "isnad_fragment"
    if _ABBREV_RE.match(name):
        return "book_abbrev"
    if _NUMBERED_RE.match(name):
        return "editorial"
    if len(name) > _LONG_MIN_CHARS:
        return "long_entry"
    return "clean"


def _source_label(source: dict[str, Any]) -> str:
    """Compose the human source label from a raw source dict."""
    label = source.get("title_en") or source.get("title", "") or ""
    volume = source.get("volume")
    return f"{label} v{volume}" if volume else label


def _rijal_row(index: int, entry: dict[str, Any]) -> dict[str, Any]:
    """Project one raw corpus record into a served rijal row dict."""
    reliability = entry.get("reliability") or []
    rel0 = reliability[0] if reliability else {}
    grade = rel0.get("grade_numeric", "")
    name = entry.get("full_name", "") or ""
    return {
        "id": index,
        "full_name": name,
        "kunya": entry.get("kunya") or "",
        "nisba": entry.get("nisba") or "",
        "tradition": entry.get("tradition", "") or "",
        "death_year": entry.get("death_year") or "",
        "birth_year": entry.get("birth_year") or "",
        "category": _classify(name),
        "teacher_count": len(entry.get("teacher_names") or []),
        "student_count": len(entry.get("student_names") or []),
        "reliability_term": rel0.get("term", "") or "",
        "reliability_grade": "" if grade in ("", None) else str(grade),
        "evaluator": rel0.get("evaluator", "") or "",
        "source_label": _source_label(entry.get("source") or {}),
        "book_path": entry.get("book_path", "") or "",
    }


def _canonical_row(entry: dict[str, Any]) -> dict[str, Any]:
    """Project one raw canonical profile into a served canonical row dict."""
    return {
        "canonical_id": entry.get("canonical_id"),
        "full_name": entry.get("full_name", "") or "",
        "kunya": entry.get("kunya") or "",
        "nisba": entry.get("nisba") or "",
        "tradition": entry.get("tradition", "") or "",
        "death_year": entry.get("death_year"),
        "birth_year": entry.get("birth_year"),
        "entry_count": entry.get("entry_count", 1),
        "source_count": len(entry.get("sources") or []),
        "teacher_count": len(entry.get("teacher_names") or []),
        "student_count": len(entry.get("student_names") or []),
        "merge_confidence": entry.get("merge_confidence"),
    }


def _load_array(path: Path) -> list[Any]:
    """Read a JSON-array corpus file into memory, failing loud if absent."""
    if not path.exists():
        raise SystemExit(f"Corpus file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise SystemExit(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return data


def build(corpus_path: Path, canonical_path: Path, out_path: Path) -> tuple[int, int]:
    """Materialize ``out_path`` from the corpus files; return ``(n_rijal, n_canon)``."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    con = registry.create_artifact(out_path)
    try:
        rijal_rows = [_rijal_row(i, e) for i, e in enumerate(_load_array(corpus_path))]
        with con:
            registry.insert_rijal(con, rijal_rows)
        canon_rows = [
            _canonical_row(e)
            for e in _load_array(canonical_path)
            if e.get("canonical_id") is not None
        ]
        with con:
            registry.insert_canonical(con, canon_rows)
        registry.finalize(con)
    finally:
        con.close()
    return len(rijal_rows), len(canon_rows)


def main() -> None:
    """Parse args, (re)build the registry artifact, report row counts."""
    parser = argparse.ArgumentParser(description="Build the narrator registry SQLite artifact.")
    parser.add_argument("--corpus", type=Path, default=_DEFAULT_CORPUS)
    parser.add_argument("--canonical", type=Path, default=_DEFAULT_CANONICAL)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = parser.parse_args()

    t0 = time.monotonic()
    n_rijal, n_canon = build(args.corpus, args.canonical, args.out)
    elapsed = time.monotonic() - t0
    print(f"Built {args.out} in {elapsed:.1f}s: {n_rijal} rijal, {n_canon} canonical")


if __name__ == "__main__":
    main()
