"""Build layer: materialize the read-only narrator registry artifact.

Schema, INSERT statements, and the Postgres-side extraction queries that turn
sol-next3's narrator store (Postgres, read-only) into ``data/registry.db``.
This is the WRITE side; the served queries live in
``backend.repositories.registry``. The connection lifecycle and CLI shell live
in ``backend.build.runner``. CENTRAL-005 permits the DDL/INSERT/SELECT SQL
here and in no other build module.

The authoritative tables are projected one-to-one: ``narrator``,
``narrator_alias``, ``claim`` (subject_type NARRATOR only), and
``transmission_edge`` joined to ``source`` for the human-readable
``source_label``. Claims keep their ``value_json`` as text (the serving layer
decodes the GRADE payloads); edges keep ``evidence`` as text the same way.
"""

from __future__ import annotations

from typing import Final

NARRATOR_SCHEMA: str = """
CREATE TABLE narrator (
  id               INTEGER PRIMARY KEY,
  primary_name_ar  TEXT NOT NULL,
  primary_name_en  TEXT,
  kunya            TEXT,
  nisba            TEXT,
  tradition        TEXT,
  birth_year_ah    INTEGER,
  death_year_ah    INTEGER,
  death_year_ce    TEXT,
  tabaqa           TEXT,
  living_city      TEXT,
  death_place      TEXT,
  category         TEXT NOT NULL,
  merge_confidence REAL
);
CREATE TABLE narrator_alias (
  id              INTEGER PRIMARY KEY,
  narrator_id     INTEGER NOT NULL REFERENCES narrator(id),
  name_ar         TEXT NOT NULL,
  name_normalized TEXT NOT NULL,
  name_role       TEXT,
  source_label    TEXT
);
CREATE INDEX ix_narrator_alias_norm ON narrator_alias (narrator_id, name_normalized);
CREATE TABLE narrator_claim (
  id            INTEGER PRIMARY KEY,
  narrator_id   INTEGER NOT NULL REFERENCES narrator(id),
  claim_type    TEXT NOT NULL,
  predicate     TEXT,
  value_text    TEXT,
  value_json    TEXT,
  source_label  TEXT,
  review_status TEXT NOT NULL
);
CREATE INDEX ix_narrator_claim ON narrator_claim (narrator_id, claim_type);
CREATE TABLE narrator_edge (
  from_id       INTEGER NOT NULL,
  to_id         INTEGER NOT NULL,
  source_label  TEXT NOT NULL,
  confidence    REAL,
  evidence_json TEXT,
  PRIMARY KEY (from_id, to_id, source_label)
);
CREATE INDEX ix_narrator_edge_rev ON narrator_edge (to_id);
CREATE TABLE narrator_source (
  id        INTEGER PRIMARY KEY,
  kind      TEXT,
  label     TEXT,
  citation  TEXT,
  version   TEXT
);
"""

_NARRATOR_INSERT = """
INSERT INTO narrator
  (id, primary_name_ar, primary_name_en, kunya, nisba, tradition, birth_year_ah,
   death_year_ah, death_year_ce, tabaqa, living_city, death_place, category,
   merge_confidence)
VALUES
  (:id, :primary_name_ar, :primary_name_en, :kunya, :nisba, :tradition,
   :birth_year_ah, :death_year_ah, :death_year_ce, :tabaqa, :living_city,
   :death_place, :category, :merge_confidence)
"""

_ALIAS_INSERT = """
INSERT INTO narrator_alias
  (id, narrator_id, name_ar, name_normalized, name_role, source_label)
VALUES
  (:id, :narrator_id, :name_ar, :name_normalized, :name_role, :source_label)
"""

_CLAIM_INSERT = """
INSERT INTO narrator_claim
  (id, narrator_id, claim_type, predicate, value_text, value_json, source_label,
   review_status)
VALUES
  (:id, :narrator_id, :claim_type, :predicate, :value_text, :value_json,
   :source_label, :review_status)
"""

_EDGE_INSERT = """
INSERT INTO narrator_edge
  (from_id, to_id, source_label, confidence, evidence_json)
VALUES
  (:from_id, :to_id, :source_label, :confidence, :evidence_json)
"""

_SOURCE_INSERT = """
INSERT INTO narrator_source
  (id, kind, label, citation, version)
VALUES
  (:id, :kind, :label, :citation, :version)
"""

TABLES: dict[str, str] = {
    "narrator": _NARRATOR_INSERT,
    "narrator_alias": _ALIAS_INSERT,
    "narrator_claim": _CLAIM_INSERT,
    "narrator_edge": _EDGE_INSERT,
    "narrator_source": _SOURCE_INSERT,
}

LIVE_NARRATOR_COUNT: Final[str] = "SELECT count(*) FROM narrator"
"""Completeness-guard count read by scripts/build_registry.py.

The artifact must carry a plausible share of the live narrator rows; the
query lives here with the rest of the extraction SQL per the
SQL-centralization rule.
"""

NARRATOR_QUERIES: dict[str, str] = {
    "narrator": """
SELECT json_build_object(
         'id', n.id, 'primary_name_ar', n.primary_name_ar,
         'primary_name_en', n.primary_name_en, 'kunya', n.kunya,
         'nisba', n.nisba, 'tradition', n.tradition,
         'birth_year_ah', n.birth_year_ah, 'death_year_ah', n.death_year_ah,
         'death_year_ce', n.death_year_ce::text, 'tabaqa', n.tabaqa,
         'living_city', n.living_city, 'death_place', n.death_place,
         'category', n.category, 'merge_confidence', n.merge_confidence)
FROM narrator n
ORDER BY n.id
""",
    "narrator_alias": """
SELECT json_build_object(
         'id', a.id, 'narrator_id', a.narrator_id, 'name_ar', a.name_ar,
         'name_normalized', a.name_normalized, 'name_role', a.name_role,
         'source_label', s.label)
FROM narrator_alias a
JOIN source s ON s.id = a.source_id
ORDER BY a.id
""",
    "narrator_claim": """
SELECT json_build_object(
         'id', c.id, 'narrator_id', c.subject_id, 'claim_type', c.claim_type,
         'predicate', c.predicate, 'value_text', c.value_text,
         'value_json', c.value_json::text, 'source_label', s.label,
         'review_status', c.review_status)
FROM claim c
JOIN source s ON s.id = c.source_id
WHERE c.subject_type = 'NARRATOR'
ORDER BY c.id
""",
    "narrator_edge": """
SELECT json_build_object(
         'from_id', e.from_narrator_id, 'to_id', e.to_narrator_id,
         'source_label', s.label, 'confidence', e.confidence,
         'evidence_json', e.evidence::text)
FROM transmission_edge e
JOIN source s ON s.id = e.source_id
ORDER BY e.from_narrator_id, e.to_narrator_id, e.source_id
""",
    "narrator_source": """
SELECT json_build_object(
         'id', s.id, 'kind', s.kind, 'label', s.label, 'citation', s.citation,
         'version', s.version)
FROM source s
ORDER BY s.id
""",
}
