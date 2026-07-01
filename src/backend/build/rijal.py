"""Build layer: materialize the read-only narrator registry artifact.

Schema, INSERT statements, and row projections that turn sol-next's
pipeline-produced rijal/canonical JSON into ``data/registry.db``. This is
the WRITE side; the served queries live in ``backend.repositories.registry``.
The connection lifecycle and CLI shell live in ``backend.build.runner``.
CENTRAL-005 permits the DDL/INSERT SQL here; the classification patterns
compile through ``backend.patterns.cached_compile`` (CENTRAL-002).

The quality-classification thresholds mirror sol-next's
``thresholds.rijal_classify_{isnad,long}_min_chars`` so the served
``category`` matches the upstream reader's filter semantics exactly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final, cast

from backend.patterns import cached_compile

REGISTRY_SCHEMA: str = """
CREATE TABLE rijal (
  id               INTEGER PRIMARY KEY,
  full_name        TEXT NOT NULL,
  kunya            TEXT NOT NULL DEFAULT '',
  nisba            TEXT NOT NULL DEFAULT '',
  tradition        TEXT NOT NULL DEFAULT '',
  death_year       TEXT NOT NULL DEFAULT '',
  birth_year       TEXT NOT NULL DEFAULT '',
  category         TEXT NOT NULL DEFAULT 'clean',
  teacher_count    INTEGER NOT NULL DEFAULT 0,
  student_count    INTEGER NOT NULL DEFAULT 0,
  reliability_term TEXT NOT NULL DEFAULT '',
  reliability_grade TEXT NOT NULL DEFAULT '',
  evaluator        TEXT NOT NULL DEFAULT '',
  source_label     TEXT NOT NULL DEFAULT '',
  book_path        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_rijal_tradition ON rijal (tradition);
CREATE INDEX idx_rijal_category ON rijal (category);
CREATE TABLE canonical (
  canonical_id   INTEGER PRIMARY KEY,
  full_name      TEXT NOT NULL,
  kunya          TEXT NOT NULL DEFAULT '',
  nisba          TEXT NOT NULL DEFAULT '',
  tradition      TEXT NOT NULL DEFAULT '',
  death_year     INTEGER,
  birth_year     INTEGER,
  entry_count    INTEGER NOT NULL DEFAULT 1,
  source_count   INTEGER NOT NULL DEFAULT 0,
  teacher_count  INTEGER NOT NULL DEFAULT 0,
  student_count  INTEGER NOT NULL DEFAULT 0,
  merge_confidence REAL
);
CREATE INDEX idx_canonical_tradition ON canonical (tradition);
"""

_RIJAL_INSERT = """
INSERT INTO rijal
  (id, full_name, kunya, nisba, tradition, death_year, birth_year, category,
   teacher_count, student_count, reliability_term, reliability_grade,
   evaluator, source_label, book_path)
VALUES
  (:id, :full_name, :kunya, :nisba, :tradition, :death_year, :birth_year, :category,
   :teacher_count, :student_count, :reliability_term, :reliability_grade,
   :evaluator, :source_label, :book_path)
"""

_CANONICAL_INSERT = """
INSERT INTO canonical
  (canonical_id, full_name, kunya, nisba, tradition, death_year, birth_year,
   entry_count, source_count, teacher_count, student_count, merge_confidence)
VALUES
  (:canonical_id, :full_name, :kunya, :nisba, :tradition, :death_year, :birth_year,
   :entry_count, :source_count, :teacher_count, :student_count, :merge_confidence)
"""

TABLES: dict[str, str] = {"rijal": _RIJAL_INSERT, "canonical": _CANONICAL_INSERT}

_ISNAD_MIN_CHARS: Final[int] = 60
_LONG_MIN_CHARS: Final[int] = 80

_REF_RE = cached_compile(r"\[\s*\d+\s*:\s*\d+|ح\s+\d{3,}")
_ISNAD_RE = cached_compile(r"(?:روى عن|سمع|حدث)")
_ABBREV_RE = cached_compile(r"^[دمسعق]\s+\(")
_NUMBERED_RE = cached_compile(r"^\d{3,}")


def classify(name: str) -> str:
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


def rijal_row(index: int, entry: dict[str, Any]) -> dict[str, Any]:
    """Project one raw corpus record into a served rijal row dict."""
    reliability: list[dict[str, Any]] = entry.get("reliability") or []
    rel0: dict[str, Any] = reliability[0] if reliability else {}
    grade: Any = rel0.get("grade_numeric", "")
    name: str = entry.get("full_name", "") or ""
    teachers: list[Any] = entry.get("teacher_names") or []
    students: list[Any] = entry.get("student_names") or []
    return {
        "id": index,
        "full_name": name,
        "kunya": entry.get("kunya") or "",
        "nisba": entry.get("nisba") or "",
        "tradition": entry.get("tradition", "") or "",
        "death_year": entry.get("death_year") or "",
        "birth_year": entry.get("birth_year") or "",
        "category": classify(name),
        "teacher_count": len(teachers),
        "student_count": len(students),
        "reliability_term": rel0.get("term", "") or "",
        "reliability_grade": "" if grade in ("", None) else str(grade),
        "evaluator": rel0.get("evaluator", "") or "",
        "source_label": _source_label(entry.get("source") or {}),
        "book_path": entry.get("book_path", "") or "",
    }


def canonical_row(entry: dict[str, Any]) -> dict[str, Any]:
    """Project one raw canonical profile into a served canonical row dict."""
    sources: list[Any] = entry.get("sources") or []
    teachers: list[Any] = entry.get("teacher_names") or []
    students: list[Any] = entry.get("student_names") or []
    return {
        "canonical_id": entry.get("canonical_id"),
        "full_name": entry.get("full_name", "") or "",
        "kunya": entry.get("kunya") or "",
        "nisba": entry.get("nisba") or "",
        "tradition": entry.get("tradition", "") or "",
        "death_year": entry.get("death_year"),
        "birth_year": entry.get("birth_year"),
        "entry_count": entry.get("entry_count", 1),
        "source_count": len(sources),
        "teacher_count": len(teachers),
        "student_count": len(students),
        "merge_confidence": entry.get("merge_confidence"),
    }


def load_array(path: Path) -> list[Any]:
    """Read a JSON-array corpus file into memory, failing loud if absent."""
    if not path.exists():
        raise SystemExit(f"Corpus file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        data: Any = json.load(fh)
    if not isinstance(data, list):
        raise SystemExit(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return cast("list[Any]", data)
