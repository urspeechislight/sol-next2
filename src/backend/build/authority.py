"""Build layer: materialize the enriched authoritative person corpus.

Turns sol-next's pipeline-produced rijal corpus (per-entry JSONL), canonical
dedup (``canonical.json``), and history corpus (event records) into the
``person`` / ``person_edge`` / ``person_event`` tables of ``registry.db``.
This supersedes the thin ``canonical`` projection: one ``person`` row per
distinct narrator carrying VALIDATED, CONSOLIDATED attributes cross-checked
across its source entries, not raw upstream values.

Three corrections happen here that the raw canonical dedup lacks:
  * junk exclusion  - isnad chain fragments, book titles, and theophoric
    truncations that are not people are dropped, not served (``is_person_name``).
  * identity resolution - each entry is keyed by ``_identity_parse`` (leading name
    unit + nasab chain, discriminating nisba). Distinct grandfather chains or nisbas
    make distinct people so pooled grades attach to the right man, while a SPECIFIC
    key (grandfather chain or appended nisba) merges one narrator's entries across
    canonical buckets so a prolific narrator is one record, not many fragments; a
    bare ism+father, lone kunya, or title stays bucket-local so common names never fuse.
  * death reconciliation - a two-digit year is folded into the century that
    ends in it (72 under 172), with a conflict flag when sources disagree.

Confident history events (a hijri year or a gazetteer match) attach as
``person_event``, disambiguated by name distinctiveness or a death-year match
so a common name does not inherit another person's battles. Teacher/student
names are filtered against the corpus of real people and linked to a person id
when known (``person_edge``). CENTRAL-005 permits the DDL/INSERT SQL here; the
classification regex compiles through ``backend.patterns.cached_compile``
(CENTRAL-002).
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

import ijson

from backend.build.grade_extract import deep_link, load_book_pages, validate_grade
from backend.build.name_registry import clean_name, is_person_name
from backend.build.transliterate import transliterate
from backend.patterns import normalize_arabic

_ARABIC_SEP: Final[str] = "_Arabic_"
_JSON_SUFFIX: Final[str] = ".json"
_LINKS: Final[frozenset[str]] = frozenset(normalize_arabic(w) for w in ("بن", "ابن", "بنت", "ابنة"))
_COMPOUND_LEADS: Final[frozenset[str]] = frozenset(
    normalize_arabic(w) for w in ("عبد", "عبيد", "أبي", "ابي", "أبو", "ابو", "أم", "ام")
)
_KUNYA_LEADS: Final[frozenset[str]] = frozenset(
    normalize_arabic(w) for w in ("أبو", "ابو", "أبي", "ابي", "أبا", "ابا", "أم", "ام", "ابن")
)
_NISBA_PREFIX: Final[str] = "ال"
_PROPHET_MARKERS: Final[frozenset[str]] = frozenset(
    normalize_arabic(w) for w in ("رسول الله", "النبي", "النبى")
)
_COMPANION_DEATH_MAX: Final[int] = 110

_DISTINCTIVE_NAME_TOKENS: Final[int] = 4
_HISTORY_ID_BASE: Final[int] = 1_000_000
_OVER_MERGE_ROOT_MAX: Final[int] = 2
_OVER_MERGE_PLACE_MAX: Final[int] = 4
_NAME_ROOT_TOKENS: Final[int] = 2
_THEOPHORIC_KUNYA_TOKENS: Final[int] = 3
_MAX_VARIANTS: Final[int] = 8
_MAX_RELIABILITY: Final[int] = 10
_MAX_PLACES: Final[int] = 6
_MAX_SOURCE_BOOKS: Final[int] = 12
_MAX_BIO_CHARS: Final[int] = 600

PERSON_SCHEMA: Final[str] = """
CREATE TABLE person (
  person_id      INTEGER PRIMARY KEY,
  full_name      TEXT NOT NULL,
  name_norm      TEXT NOT NULL DEFAULT '',
  name_variants  TEXT NOT NULL DEFAULT '',
  kunya          TEXT NOT NULL DEFAULT '',
  nisba          TEXT NOT NULL DEFAULT '',
  birth_year     INTEGER,
  death_year     INTEGER,
  death_conflict INTEGER NOT NULL DEFAULT 0,
  tradition      TEXT NOT NULL DEFAULT '',
  stance         TEXT NOT NULL DEFAULT '',
  reliability    TEXT NOT NULL DEFAULT '[]',
  places         TEXT NOT NULL DEFAULT '',
  source_books   TEXT NOT NULL DEFAULT '',
  n_sources      INTEGER NOT NULL DEFAULT 0,
  teacher_count  INTEGER NOT NULL DEFAULT 0,
  student_count  INTEGER NOT NULL DEFAULT 0,
  event_count    INTEGER NOT NULL DEFAULT 0,
  bio            TEXT NOT NULL DEFAULT '',
  confidence     TEXT NOT NULL DEFAULT 'medium',
  generation     TEXT NOT NULL DEFAULT '',
  name_latin     TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_person_name_norm ON person (name_norm);
CREATE INDEX idx_person_kunya ON person (kunya);
CREATE INDEX idx_person_tradition ON person (tradition);
CREATE INDEX idx_person_confidence ON person (confidence);
CREATE TABLE person_edge (
  person_id       INTEGER NOT NULL,
  relation        TEXT NOT NULL,
  name            TEXT NOT NULL,
  other_person_id INTEGER
);
CREATE INDEX idx_edge_person ON person_edge (person_id);
CREATE TABLE person_event (
  person_id  INTEGER NOT NULL,
  event      TEXT NOT NULL DEFAULT '',
  event_type TEXT NOT NULL DEFAULT '',
  year_ah    INTEGER,
  role       TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_event_person ON person_event (person_id);
CREATE TABLE person_grade (
  person_id INTEGER NOT NULL,
  evaluator TEXT NOT NULL DEFAULT '',
  term      TEXT NOT NULL DEFAULT '',
  book      TEXT NOT NULL DEFAULT '',
  page      INTEGER,
  link      TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_grade_person ON person_grade (person_id);
"""

_PERSON_INSERT: Final[str] = (
    "INSERT INTO person (person_id, full_name, name_norm, name_variants, kunya, nisba,"
    " birth_year, death_year, death_conflict, tradition, stance, reliability, places,"
    " source_books, n_sources, teacher_count, student_count, event_count, bio, confidence,"
    " generation, name_latin)"
    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)
_EDGE_INSERT: Final[str] = "INSERT INTO person_edge (person_id, relation, name, other_person_id) VALUES (?,?,?,?)"
_EVENT_INSERT: Final[str] = "INSERT INTO person_event (person_id, event, event_type, year_ah, role) VALUES (?,?,?,?,?)"
_GRADE_INSERT: Final[str] = (
    "INSERT INTO person_grade (person_id, evaluator, term, book, page, link) VALUES (?,?,?,?,?,?)"
)

TABLES: Final[dict[str, str]] = {
    "person": _PERSON_INSERT, "person_edge": _EDGE_INSERT,
    "person_event": _EVENT_INSERT, "person_grade": _GRADE_INSERT,
}


def clean_ws(name: str) -> str:
    """Collapse embedded newlines and runs of whitespace in a display name."""
    return " ".join(name.split())


def reconcile_death(years: Counter[int]) -> tuple[int | None, bool]:
    """Return (death year, conflict). Fold a two-digit year into a 1XX that ends in it."""
    if not years:
        return None, False
    vals = set(years)
    folded: Counter[int] = Counter()
    for year, count in years.items():
        target = year
        if year < 100:
            three = next((v for v in vals if v >= 100 and v % 100 == year), None)
            target = three if three is not None else year
        folded[target] += count
    top = folded.most_common()
    conflict = len([y for y in folded if y]) > 1 and top[0][1] < sum(folded.values())
    return top[0][0], conflict


def _name_root(name: str) -> tuple[str, ...]:
    """The ism + father core of a name (its first significant tokens), for identity grouping."""
    significant = [t for t in normalize_arabic(clean_name(name)).split() if t not in _LINKS]
    return tuple(significant[:_NAME_ROOT_TOKENS])


def is_over_merge(entries: list[dict[str, Any]]) -> bool:
    """True when a canonical bucket fuses several distinct people (a shared-kunya collision).

    A death conflict or a nisba variant alone does not qualify: sources disagree on
    one person's death (Sufyan b. Uyayna, 191 vs 198) and record extra nisbas. Two
    signals do qualify: many distinct name roots (a shared-kunya bucket fusing
    بكر بن الحكم, سلمة بن علقمة, ...), OR many distinct residences on a single name
    root (same-name people from different cities fused, e.g. al-Husayn b. Ibrahim
    recorded as قمي / بغدادي / خراساني / همداني — one lifetime is not five cities).
    """
    roots = {_name_root(e["full_name"]) for e in entries
             if e.get("full_name") and is_person_name(e["full_name"])}
    roots.discard(())
    places = {loc if isinstance(loc, str) else str(loc)
              for e in entries for loc in (e.get("locations") or [])}
    return len(roots) > _OVER_MERGE_ROOT_MAX or len(places) > _OVER_MERGE_PLACE_MAX


def _leading_unit(toks: list[str]) -> int:
    """Length of the leading name unit before the nasab chain: kunya, theophoric ism, or plain ism.

    A kunya-led name (``أبو بكر …``, ``ابن عمر …``) carries no ism at token 0, so the two-token
    kunya IS the identifying head; ``أبو عبد الله`` extends to three when the second token is a
    theophoric lead. A compound ism (``عبد الله …``) takes two tokens; any other ism takes one.
    Without this, the نسب walk (which expects ``بن`` right after a one-token ism) never starts on a
    kunya-led name and every ``أبو``-led narrator collapses to the same one-token key.
    """
    if not toks:
        return 0
    if toks[0] in _KUNYA_LEADS:
        return _THEOPHORIC_KUNYA_TOKENS if len(toks) > 1 and toks[1] in _COMPOUND_LEADS else 2
    if toks[0] in _COMPOUND_LEADS:
        return 2
    return 1


def _identity_parse(name: str) -> tuple[tuple[str, ...], bool]:
    """Return ``(identity key, specific)`` for a narrator name.

    The key is the leading name unit plus the nasab chain, with the first nisba appended only when
    the nasab is just the father. The head is the ism for an ism-led name and the kunya for a
    kunya-led one (``_leading_unit``). Two men who share a head are told apart by a distinct
    grandfather chain (بن أبي نمر vs بن رفاعة) or, absent one, a distinct primary nisba (النخعي vs
    الجعفي), while trailing laqab / residence / grading tokens fall past the key so surface variants
    of one man collapse. ``specific`` is true when the key carries a grandfather chain (depth >= 2)
    or a genuinely appended nisba; that is the signal it names one man precisely enough to merge his
    entries across canonical buckets. A bare ism+father, a lone kunya, or a title (الشيخ) is NOT
    specific: those keys stay bucket-local so common names and honorifics never fuse into one person.
    """
    toks = normalize_arabic(clean_name(name)).split()
    if not toks:
        return (), False
    j = _leading_unit(toks)
    depth = 0
    while j < len(toks) and toks[j] in _LINKS:
        nxt = j + 1
        j = nxt + 2 if (nxt < len(toks) and toks[nxt] in _COMPOUND_LEADS) else nxt + 1
        depth += 1
    key = toks[:j]
    nisba_appended = False
    if depth <= 1 and j < len(toks) and toks[j].startswith(_NISBA_PREFIX):
        key = toks[: j + 1]
        nisba_appended = True
    return tuple(key), (depth >= 2 or nisba_appended)


def _combine_tradition(counter: Counter[str]) -> str:
    """Fold the traditions of a merged person's source buckets into one label; mixed sunni+shia is ``both``."""
    present = set(counter)
    if "both" in present or {"sunni", "shia"} <= present:
        return "both"
    for tradition in ("sunni", "shia", "history"):
        if tradition in present:
            return tradition
    return ""


def _as_stance(value: Any) -> str:
    """Coerce a raw stance entry (string or dict) to its stance token."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("stance"))
    return str(value)


def _generation(categories: list[str], teacher_names: set[str], death_year: int | None) -> str:
    """Derive the narrator generation from source category tags and named teachers.

    ``صحابي`` among the categories marks a Companion (ṣaḥābī); the Prophet among the
    teachers he heard from confirms one only when the death year is early enough to
    be plausible (a polluted ``رسول الله`` edge must not tag a 128 AH narrator);
    ``تابع التابعين`` a follower's follower; ``تابعي`` a Successor (tābiʿī).
    """
    joined = normalize_arabic(" ".join(categories))
    if "صحاب" in joined:
        return "companion"
    heard_prophet = any(
        any(marker in normalize_arabic(name) for marker in _PROPHET_MARKERS)
        for name in teacher_names
    )
    if heard_prophet and (death_year is None or death_year <= _COMPANION_DEATH_MAX):
        return "companion"
    if "تابع التابع" in joined:
        return "successor_of_successors"
    if "تابع" in joined:
        return "successor"
    return ""


def _matched_events(
    name_norm: str, dyear: int | None, hist_events: dict[str, list[tuple[dict[str, Any], int | None]]]
) -> list[dict[str, Any]]:
    """Select history events safe to attribute: a distinctive name, or a death-year match."""
    candidate = hist_events.get(name_norm, [])
    significant = len([t for t in name_norm.split() if t not in _LINKS])
    if significant >= _DISTINCTIVE_NAME_TOKENS:
        return [ev for ev, _ in candidate]
    if dyear is not None:
        return [ev for ev, hist_death in candidate if hist_death == dyear]
    return []


def _person_rows(
    pid: int,
    entries: list[dict[str, Any]],
    tradition: str,
    display_name: str,
    pid_by_name: dict[str, int],
    hist_events: dict[str, list[tuple[dict[str, Any], int | None]]],
    grade_fn: Callable[[list[dict[str, Any]], str], list[dict[str, Any]]],
) -> tuple[tuple[Any, ...], list[tuple[Any, ...]], list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    """Aggregate one person's entries into (person row, edge rows, event rows, grade rows).

    Reliability is not trusted from the raw extraction: ``grade_fn`` re-validates each
    grade against its cited source page and returns only the grades that survive, each
    already carrying a reader deep-link. The person's ``reliability`` summary column and
    the ``person_grade`` rows are both derived from that single validated set. ``pid_by_name``
    maps a normalized clean name to the person id it resolved to, so a teacher/student edge
    links to that person when known.
    """
    kunyas = Counter(e["kunya"] for e in entries if e.get("kunya"))
    nisbas = Counter(e["nisba"] for e in entries if e.get("nisba"))
    births = Counter(e["birth_year"] for e in entries if e.get("birth_year"))
    dyear, conflict = reconcile_death(Counter(e["death_year"] for e in entries if e.get("death_year")))
    display = clean_name(display_name)
    variants = list(dict.fromkeys(clean_name(e["full_name"]) for e in entries if e.get("full_name")))[:_MAX_VARIANTS]
    graded = grade_fn(entries, display)
    reliability = list(dict.fromkeys(f"{g['evaluator']}={g['term']}" for g in graded))
    grades = [(pid, g["evaluator"], g["term"], g["book"], g["page"], g["link"]) for g in graded]
    stance = Counter(_as_stance(s) for e in entries for s in (e.get("stance") or []))
    places = list(dict.fromkeys(loc if isinstance(loc, str) else str(loc)
                                for e in entries for loc in (e.get("locations") or [])))
    src = list(dict.fromkeys(e["source"].get("title") for e in entries if e.get("source")))
    bio = max((e.get("bio_text") or "" for e in entries), key=len, default="")
    over_merged = is_over_merge(entries)
    confidence = "low" if over_merged else ("high" if (kunyas or nisbas) and dyear else "medium")
    name_norm = normalize_arabic(display)
    edges: list[tuple[Any, ...]] = []
    for relation, field in (("teacher", "teacher_names"), ("student", "student_names")):
        for name in dict.fromkeys(n for e in entries for n in (e.get(field) or [])):
            clean = clean_name(name)
            clean_norm = normalize_arabic(clean)
            if is_person_name(name) and clean_norm != name_norm:
                edges.append((pid, relation, clean, pid_by_name.get(clean_norm)))
    teacher_count = sum(1 for edge in edges if edge[1] == "teacher")
    student_count = sum(1 for edge in edges if edge[1] == "student")
    stance_out = "" if over_merged else (stance.most_common(1)[0][0] if stance else "")
    generation = _generation([c for e in entries for c in (e.get("categories") or [])],
                             {n for e in entries for n in (e.get("teacher_names") or [])}, dyear)
    matched = _matched_events(name_norm, dyear, hist_events)
    events = [(pid, ev.get("event") or "", ev.get("event_type") or "",
               ev.get("year_ah") if isinstance(ev.get("year_ah"), int) else None,
               ev.get("marker_keyword") or "")
              for ev in {(e.get("event"), e.get("event_type"), e.get("year_ah"), e.get("marker_keyword")): e
                         for e in matched}.values()]
    row = (pid, display, name_norm, " | ".join(variants),
           kunyas.most_common(1)[0][0] if kunyas else "",
           nisbas.most_common(1)[0][0] if nisbas else "",
           births.most_common(1)[0][0] if births else None, dyear, int(conflict),
           tradition or "", stance_out,
           json.dumps(reliability[:_MAX_RELIABILITY], ensure_ascii=False),
           " | ".join(places[:_MAX_PLACES]), " | ".join(str(s) for s in src[:_MAX_SOURCE_BOOKS]),
           len(entries), teacher_count, student_count, len(matched), bio[:_MAX_BIO_CHARS],
           confidence, generation, transliterate(display))
    return row, edges, events, grades


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL corpus file into a list of entry dicts, failing loud if absent."""
    if not path.exists():
        raise SystemExit(f"Corpus file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _stream_history(
    path: Path, real_names: set[str]
) -> tuple[dict[str, list[tuple[dict[str, Any], int | None]]], dict[tuple[str, int | None], dict[str, Any]]]:
    """Stream history event records into (linked-narrator events, history-only persons keyed by name+death)."""
    if not path.exists():
        raise SystemExit(f"History corpus not found: {path}")
    linked: dict[str, list[tuple[dict[str, Any], int | None]]] = defaultdict(list)
    history_only: dict[tuple[str, int | None], dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for person in ijson.items(handle, "item"):
            events = person.get("events") or []
            if not events:
                continue
            name = (person.get("full_name") or "").strip()
            name_norm = normalize_arabic(name)
            hist_death = person.get("death_year") if isinstance(person.get("death_year"), int) else None
            good = [ev for ev in events if ev.get("year_ah") or ev.get("gazetteer_match")]
            if name_norm in real_names:
                for ev in good:
                    linked[name_norm].append((ev, hist_death))
            elif good and is_person_name(name):
                key = (name_norm, hist_death)
                record = history_only.get(key)
                if record is None:
                    history_only[key] = {"name": name, "kunya": person.get("kunya") or "",
                                         "nisba": person.get("nisba") or "", "death": hist_death,
                                         "events": list(good)}
                else:
                    record["events"].extend(good)
    return linked, history_only


def _source_map(books_dir: Path) -> dict[str, str]:
    """Map each source book's ``sol_id`` work-id to its path relative to ``books_dir``.

    The map is derived from the filenames under ``books_dir``: every book is named
    ``<...>_Arabic_<sol_id>.json`` and its trailing token is exactly the ``frontmatter.sol_id``
    a grade cites as ``work_id`` (verified against the file metadata). A grade whose work-id is
    absent here has no locatable source page and cannot be validated.
    """
    out: dict[str, str] = {}
    for path in books_dir.rglob("*.json"):
        work_id = path.name.split(_ARABIC_SEP)[-1].removesuffix(_JSON_SUFFIX)
        if work_id:
            out[work_id] = str(path.relative_to(books_dir))
    return out


def _grade_validator(
    sources: dict[str, str], books_dir: Path
) -> Callable[[list[dict[str, Any]], str], list[dict[str, Any]]]:
    """Build a closure that keeps only grades validated against their cited source page.

    Each source book's pages are read once and cached. For every reliability grade whose
    ``source`` names a known book and page, the grade survives only when ``validate_grade``
    confirms its term sits in the correct critic's segment of the narrator's own entry, and
    a survivor carries a relative reader deep-link to where it is recorded. A grade citing an
    unknown book, or one that does not validate, is dropped rather than shown.
    """
    pages_cache: dict[str, dict[int, str]] = {}

    def pages_for(work_id: str) -> dict[int, str]:
        """Return the cited book's ``{page: text}`` map, reading and caching it once."""
        cached = pages_cache.get(work_id)
        if cached is None:
            rel = sources.get(work_id) or ""
            cached = load_book_pages(books_dir / rel) if rel else {}
            pages_cache[work_id] = cached
        return cached

    def validate(entries: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
        """Return this person's grades that validate against their source page, deduped and linked.

        A grade is located on its page using its own entry's ``full_name`` as it appears in the
        source, so it validates against the exact entry it was scraped from; the reader link then
        highlights the clean person ``name`` rather than that raw, sometimes noisy, entry string.
        """
        out: dict[tuple[str, str, str, int], dict[str, Any]] = {}
        for entry in entries:
            entry_name = entry.get("full_name") or name
            for grade in (entry.get("reliability") or []):
                src = grade.get("source") or {}
                work_id, page = src.get("work_id"), src.get("page")
                evaluator, term = grade.get("evaluator"), grade.get("term")
                if not (work_id and isinstance(page, int) and evaluator and term):
                    continue
                key = (evaluator, term, work_id, page)
                if key not in out and validate_grade(pages_for(work_id), grade, entry_name):
                    out[key] = {"evaluator": evaluator, "term": term,
                                "book": src.get("title") or work_id, "page": page,
                                "link": deep_link(work_id, page, name)}
        return list(out.values())

    return validate


def build_person_tables(
    con: sqlite3.Connection, canonical_path: Path, corpus_path: Path, history_path: Path | None,
    books_dir: Path,
) -> dict[str, int]:
    """Materialize the person / person_edge / person_event / person_grade tables; return counts.

    ``history_path`` is the optional 3.4 GB history corpus. When absent, persons
    carry no events and no history-only actors are added; the rijal enrichment
    (kunya, death, reliability, stance, edges) is built either way. ``books_dir`` roots
    the source books (``sol-next``'s ``data/books``) so every reliability grade can be
    re-validated against its cited source page before it is served.
    """
    corpus = _load_jsonl(corpus_path)
    with canonical_path.open(encoding="utf-8") as handle:
        canon = json.load(handle)
    grade_fn = _grade_validator(_source_map(books_dir), books_dir)
    real_names = {normalize_arabic(record["full_name"]) for record in canon}
    hist_events: dict[str, list[tuple[dict[str, Any], int | None]]] = {}
    history_only: dict[tuple[str, int | None], dict[str, Any]] = {}
    if history_path is not None:
        hist_events, history_only = _stream_history(history_path, real_names)

    persons: list[tuple[Any, ...]] = []
    edges: list[tuple[Any, ...]] = []
    events: list[tuple[Any, ...]] = []
    grades: list[tuple[Any, ...]] = []
    specific_buckets: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    specific_tradition: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    local_clusters: list[tuple[list[dict[str, Any]], str]] = []
    for record in canon:
        if not is_person_name(record["full_name"]):
            continue
        entries = [corpus[i] for i in record["entry_ids"] if i < len(corpus)]
        if not entries:
            continue
        tradition = record.get("tradition") or ""
        by_key: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
        specific: dict[tuple[str, ...], bool] = {}
        for entry in entries:
            full = entry.get("full_name") or ""
            if is_person_name(full):
                key, is_specific = _identity_parse(full)
                if key:
                    by_key[key].append(entry)
                    specific[key] = is_specific
        for key, cluster in by_key.items():
            if specific[key]:
                specific_buckets[key].extend(cluster)
                if tradition:
                    specific_tradition[key][tradition] += 1
            else:
                local_clusters.append((cluster, tradition))

    groups: list[tuple[int, list[dict[str, Any]], str]] = []
    pid_by_name: dict[str, int] = {}
    pid = 0
    for key, cluster in specific_buckets.items():
        pid += 1
        groups.append((pid, cluster, _combine_tradition(specific_tradition[key])))
        for entry in cluster:
            pid_by_name[normalize_arabic(clean_name(entry["full_name"]))] = pid
    for cluster, tradition in local_clusters:
        pid += 1
        groups.append((pid, cluster, tradition))
        for entry in cluster:
            pid_by_name[normalize_arabic(clean_name(entry["full_name"]))] = pid

    for person_id, cluster, tradition in groups:
        display = Counter(clean_name(e["full_name"]) for e in cluster).most_common(1)[0][0]
        row, cluster_edges, cluster_events, cluster_grades = _person_rows(
            person_id, cluster, tradition, display, pid_by_name, hist_events, grade_fn)
        persons.append(row)
        edges.extend(cluster_edges)
        events.extend(cluster_events)
        grades.extend(cluster_grades)

    hid = _HISTORY_ID_BASE
    for (_key_norm, _death), record in history_only.items():
        hid += 1
        record_events = list({(e.get("event"), e.get("event_type"), e.get("year_ah"), e.get("marker_keyword")): e
                              for e in record["events"]}.values())
        display = clean_name(record["name"])
        persons.append((hid, display, normalize_arabic(display), display,
                        record["kunya"], record["nisba"], None, record["death"], 0, "history", "",
                        "[]", "", "", 0, 0, 0, len(record_events), "", "history_person", "",
                        transliterate(display)))
        for ev in record_events:
            events.append((hid, ev.get("event") or "", ev.get("event_type") or "",
                           ev.get("year_ah") if isinstance(ev.get("year_ah"), int) else None,
                           ev.get("marker_keyword") or ""))

    con.executemany(_PERSON_INSERT, persons)
    con.executemany(_EDGE_INSERT, edges)
    con.executemany(_EVENT_INSERT, events)
    con.executemany(_GRADE_INSERT, grades)
    return {"person": len(persons), "person_edge": len(edges),
            "person_event": len(events), "person_grade": len(grades)}
