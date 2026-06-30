# ADR-0001 — Storage contract between sol-next and sol-next2

**Date:** 2026-05-23
**Status:** Superseded by implementation divergence (2026-06-30). The consume-only contract below was never built — sol-next2 self-builds its read-only SQLite artifacts. See the update note below; a formal ADR-0002 is pending.
**Supersedes:** the implicit "sol-next2 ingests JSON into its own SQLite"
plan that briefly existed earlier in development.

> **Update (2026-06-30) — implementation diverged from this decision.** As
> recorded below, this ADR waited for `sol-next` to emit a SQLite artifact that
> sol-next2 would consume. That did not happen. sol-next2 instead became
> self-contained: it builds its own read-only SQLite artifacts (`data/corpus.db`
> FTS5, `data/registry.db`) directly from the `SOL_BOOKS_DIR` corpus root (today
> the sibling `sol-next/data/books` tree) and serves page text from that root at
> request time. There are still no external database *services* — only stdlib
> `sqlite3` opened read-only/immutable — so the "zero runtime database services"
> intent holds, but the "raw pre-pipeline files never enter sol-next2's storage"
> carve-out below is **not** honored by the current code. A formal ADR-0002 will
> record the self-contained contract. The body below is preserved as the
> original 2026-05-23 record.

## Context

sol-next2 is a read-only reading interface that serves data produced by
the upstream `sol-next` pipeline (5 phases: ingest → segment → extract →
enrich → graph). The pipeline currently declares Postgres, Neo4j,
Qdrant, and Redis as storage targets in its `pyproject.toml`. Phase 5
(`graph`) is intended to write edges to Neo4j and embeddings to Qdrant.

As of today:

- Phases 3, 4, 5 are **stubs** in sol-next ("contract defined, not yet
  built" per `sol-next/docs/architecture.md`).
- sol-next has never been run against the full corpus.
- No Postgres/Neo4j/Qdrant instances exist locally.
- sol-next2 serves curated JSON (~30 KB, 8 books, 1 sample page) from
  `data/`.

A full council review (see `docs/councils/2026-05-23-storage-stack-*`)
considered: Postgres + pgvector + AGE; Postgres + Neo4j + Meilisearch;
"just Postgres"; static file; status quo. Five advisors, five
independent peer reviews.

## Decision

When sol-next phases 3–5 are built, **the pipeline will emit a single
versioned SQLite artifact as its public output contract** in addition to
(or instead of) its internal Neo4j / Qdrant writes. sol-next2 will
consume that artifact and nothing else.

### The contract

| Item                | Choice                                                  |
| ------------------- | ------------------------------------------------------- |
| Artifact format     | SQLite (single file)                                    |
| Indexing            | FTS5 for Arabic + English text                          |
| Vector search       | `sqlite-vec` extension                                  |
| Nested data         | JSON1 for narrators + cross-refs inside hadith rows     |
| Graph queries       | Recursive CTEs + in-memory NetworkX adjacency lists     |
| Mutability          | Read-only; atomically swapped on republish              |
| Versioning          | One artifact per pipeline run; older versions retained  |
| Distribution        | Mounted by sol-next2; no network DB protocol            |

The pipeline's existing Neo4j + Qdrant writes are retained for **other**
consumers (research notebooks, ad-hoc analytics, future tools that
genuinely need graph or vector DBs). They are not the sol-next2 contract.

### Why this shape

sol-next2's workload is read-mostly, single-writer-upstream, immutable.
That is not a database problem; it is a build-artifact distribution
problem. Running Neo4j + Qdrant + Postgres for a read-only reader is
operational overkill on a single-dev self-hosted box.

The council's First Principles read of the workload established:

1. The 8 access patterns sol-next2 needs collapse to 3 primitives —
   key/ordered lookup, inverted indexes, vector ANN.
2. Isnad chains are paths already materialized inside each hadith
   document by Phase 3 — not traversed at query time.
3. "Commentaries citing a hadith" is a reverse-index dict, not a graph
   query.
4. Tens of thousands of narrators fit in RAM as an adjacency list;
   NetworkX in-process beats Neo4j-over-network for the rare traversal.

SQLite with FTS5 + sqlite-vec + JSON1 covers all three primitives in a
single file with zero runtime services. Migration to Postgres remains a
one-day swap (the repository interface in sol-next2 already abstracts
storage), so this choice does not lock us in.

## Carve-outs

1. **Arabic FTS quality** is unproven. Postgres `tsvector` and SQLite
   FTS5 both ship mediocre defaults for classical Arabic (no root-based
   stemming, no tashkeel handling, no ta marbuta normalization). Before
   committing the artifact format, the pipeline owner must validate
   FTS5 with a custom Arabic tokenizer against real queries. If quality
   is unacceptable, **Meilisearch** is added as a *derived* index
   rebuilt from the same canonical artifact — never a second SSOT.

2. **Postgres remains the escape hatch.** The day a user hits a wall
   SQLite + adjacency lists cannot serve, sol-next2 migrates to
   Postgres (or to the existing Neo4j/Qdrant writes of sol-next). The
   migration is a repository-internal change; routes, models, and tests
   do not move.

3. **Embedding model lifecycle** belongs to sol-next, not sol-next2.
   Re-embedding millions of records on a model swap is the pipeline's
   problem; sol-next2 only reads what's in the artifact.

4. **Narrator-name normalization** (kunya / nasab / laqab variants) and
   **citation-ID stability** (Bukhari numbering, Shamela vs printed
   editions) are pipeline-side responsibilities. sol-next2 treats the
   IDs in the artifact as authoritative.

## Status (historical — superseded; see the update note at top)

**Deferred.** sol-next phases 3, 4, 5 are not yet built. There is
nothing to consume. sol-next2 continues serving curated JSON in
`data/`. When the pipeline starts producing real output, this ADR is
the spec for what to emit.

No SQL dependencies live in sol-next2's `pyproject.toml`. They will be
added (`sqlite-vec` Python bindings, optionally `networkx`) when the
artifact format is actually being read.

## Consequences

- sol-next2 has zero runtime database services. `pnpm ci` + a static
  HTTP server is the entire stack.
- The repository layer in `src/backend/repositories/` already abstracts
  storage behind `load_json(...)`. Adding a `load_sqlite(...)` reader is
  a one-file change when the artifact arrives.
- sol-next must add a new emission step to Phase 5 alongside the
  existing Neo4j + Qdrant writes. This is a pipeline-side change that
  will be tracked separately when phases 3–5 begin implementation.
- The "ingest from sol-next/data/raw.json into sol-next2's DB" path is
  permanently dead. Raw pre-pipeline files never enter sol-next2's
  storage.
