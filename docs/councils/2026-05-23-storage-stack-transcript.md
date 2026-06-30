# Council transcript — sol-next2 storage stack

**Date:** 2026-05-23 19:35 **Question source:** user invoked `/council` on the
storage-stack decision **Workspace:** `/home/dev/code/sol-next2/`

---

## Original question

> ok but why are we using sqlite, did we evaluate postgrql and pgvector to be
> used and is there a better alternative to neo4j for graph? I want you to
> council this and come up with the best solution based on council agents

## Framed question

What storage stack should the **sol-next2 backend** use to consume the
**sol-next pipeline's** output for a multilingual classical-Arabic manuscript
reading interface?

### Context

- **sol-next2 is read-only.** It does not ingest manuscripts; it reads
  structured output from the upstream sol-next pipeline (5 phases: ingest →
  segment → extract → enrich → graph).
- sol-next pipeline declares these storage targets in its `pyproject.toml`:
  `psycopg[async]>=3.1` (Postgres), `neo4j>=5.0`, `qdrant-client>=1.7`,
  `redis>=5.0`. The pipeline has **not been run against the full corpus yet**;
  none of those stores are running locally.
- **Today's v1:** static JSON files (~30KB total, 8 books, 1 sample page) loaded
  into memory at startup, served from `@functools.cache`.

### Data shape sol-next2 needs to serve

- Books: thousands eventually, 8 today
- Hadiths: millions across the corpus; each with Arabic matn, English matn,
  isnad text, parsed narrators, grade
- Narrators: tens of thousands with biographical metadata and graph edges
  (teacher-of, transmitted-from, contemporary-of)
- Cross-references: graph edges between hadiths in different collections
  (parallel narrations) + citations from later commentaries to earlier
  collections
- Page-level content: TOC + bilingual page rendering

### Access patterns

1. List books by category (filter)
2. Get one book detail (key lookup)
3. Get TOC + page content (ordered scan)
4. Get hadith with full isnad + narrators + cross-refs (joins / graph)
5. Search hadiths by Arabic or English text (FTS)
6. "Related hadiths" via semantic similarity (vector)
7. Trace a narrator's transmissions through a chain (1-5 hops)
8. All later commentaries citing a given hadith (graph edges)

### Constraints

- Single-developer, self-hosted on a Linux box (buildhost, 10.0.0.10)
- Strict SSOT/DRY culture — fewer moving parts unless multi-store earns it
- Backend FastAPI; frontend separate React

### Specific sub-questions

1. For relational/document side — Postgres + **pgvector** instead of Postgres +
   separate **Qdrant**?
2. For graph — **Neo4j**, **Apache AGE**, **Memgraph**, **ArangoDB**, or
   **Postgres recursive CTEs**?
3. Minimum store count? Is one Postgres (pgvector + AGE) realistic?
4. **SQLite** in production (e.g., embedded read-mirror per worker), or skip to
   Postgres?

---

## Anonymization mapping

| Letter | Advisor                      |
| ------ | ---------------------------- |
| A      | The Outsider                 |
| B      | The Contrarian               |
| C      | The Executor                 |
| D      | The First Principles Thinker |
| E      | The Expansionist             |

---

## Advisor responses

### The Contrarian (Response B)

Everyone is about to tell you "one Postgres, pgvector + AGE, done." That's the
seductive answer. It's also the one most likely to bite you in 18 months. Let me
name the specific failures.

**Apache AGE is a trap.** It's a Bitnine project that has been in perpetual
"almost there" status for years. Release cadence is slow, the PG18 story is
uncertain, openCypher coverage is partial, the query planner doesn't understand
graph cardinality, and the community is a fraction of Neo4j's. For pattern 7
(1-5 hop narrator transmission) and pattern 8 (commentary citation traversal) on
tens of thousands of narrators with millions of hadiths, you will hit AGE
planner pathologies — variable-length paths over `MATCH (a)-[*1..5]->(b)`
degrade badly when the optimizer can't push predicates. You'll end up writing
recursive CTEs anyway and wondering why you installed AGE. Just write the CTEs
from day one, or use Neo4j and stop pretending.

**pgvector at "millions of hadiths" with multilingual embeddings is fine — until
it isn't.** HNSW index build time on a 5M-row table with 1024-dim vectors is
hours, and you cannot rebuild without downtime unless you orchestrate it.
Filtered vector search (pattern 6 scoped to a book or grade) is where pgvector's
pre-filter vs post-filter behavior gets ugly. Qdrant handles payload filtering
natively. If "related hadiths within Sahih collections only" matters, pgvector
will quietly return wrong-feeling results.

**The Arabic FTS question nobody is asking.** Postgres `tsvector` with the
default Arabic config is mediocre. No proper root-based stemming, no handling of
diacritics (tashkeel) vs undiacritized matn, no ta marbuta normalization.
Pattern 5 will feel broken to actual Arabic readers. You need either a custom
dictionary, pg_trgm gymnastics, or — honestly — OpenSearch/Meilisearch with
proper Arabic analyzers. This is the silent killer that "one Postgres" advocates
ignore.

**SQLite as read-mirror is fine for 8 books, suicidal at thousands.** Skip it.

**My position:** Postgres for relational/document. Neo4j for graph (you have
real graph queries, not tree queries). Meilisearch or OpenSearch for Arabic FTS.
Defer vectors until pattern 6 has a real user. Three stores, each doing what
it's actually good at. The DRY tax is real; the "everything in Postgres" tax is
paid in correctness, and you won't see the bill until users complain.

### The First Principles Thinker (Response D)

The framing buries the actual question under tooling. Strip it down.

**What is sol-next2 actually doing?** Serving an immutable, append-rarely,
read-mostly corpus that some other pipeline has already finished computing. That
is not a database problem. That is a **build artifact distribution problem**.
You're not running OLTP. You're not even running analytics. You're shipping a
precomputed library catalog.

**Is the graph actually graph-shaped?** No. Look at the access patterns
honestly:

- "Narrator chain through isnad" — that's a **path** that already exists, fully
  materialized, inside each hadith document. The pipeline parsed it. You don't
  traverse it at query time; you read it. It's a list.
- "Later commentaries citing a hadith" — that's a **reverse index**:
  `hadith_id -> [citing_hadith_ids]`. A dict.
- "Parallels across collections" — same. A dict.
- "1-5 hop narrator traversal" — the only genuinely graph-shaped query, and at
  tens of thousands of nodes it fits in RAM as an adjacency list. NetworkX in a
  Python process will outrun Neo4j over the network.

There is no graph workload here. There is a **precomputed denormalized read
model** with some adjacency lists.

**Do the 8 patterns collapse?** Yes, into three primitives:

1. **Key/ordered lookup** (books, pages, hadiths by ID, TOC scan)
2. **Inverted indexes** (category, Arabic FTS, English FTS, reverse citations,
   narrator→hadiths)
3. **Vector ANN** (semantic similarity)

That's it. Everything else is a join on (1) using (2) or (3) as the entry point.

**The honest minimum stack:**

- **SQLite** as the artifact format. The pipeline emits a `.sqlite` file (with
  FTS5 built-in, sqlite-vec extension for ANN, JSON1 for nested isnad/narrator
  blobs). FastAPI opens it read-only. Done. Millions of hadiths fit comfortably;
  FTS5 is excellent for Arabic with the right tokenizer; sqlite-vec handles your
  scale trivially.
- Adjacency lists for narrators load into memory at boot. ~tens of thousands of
  nodes is nothing.

**Postgres, Neo4j, Qdrant, Redis are all wrong for sol-next2** — they assume
mutability and concurrent writers you don't have. They're the right tools for
sol-next (the _pipeline_), which is why they're in _that_ pyproject.

**The real question isn't "which 4 stores" — it's "why are you running any
servers at all for a read-only artifact?"** Ship a file. Version it. Mount it.
Move on.

### The Expansionist (Response E)

**Pick Postgres + pgvector + Apache AGE. One database. But not because it's
"fewer moving parts" — because consolidation is what unlocks the compounding
moves.**

Here's what nobody's saying: you're not building a reading app. You're building
**the first queryable graph-vector index of the classical hadith corpus in
English**. That dataset — millions of hadiths, tens of thousands of narrators,
isnad chains, cross-collection parallels, commentary citations, bilingual matn,
vector embeddings — does not exist as a unified API anywhere. Not for
researchers. Not for developers. Not for AI labs training Arabic models. The
moment you have it in _one_ queryable substrate, you are sitting on
infrastructure that several constituencies will pay for or build on.

**What one Postgres unlocks that three stores fight against:**

1. **Hybrid queries in a single SQL statement.** "Find hadiths semantically
   similar to X, narrated through Bukhari's teachers within 2 hops, graded
   sahih, with at least 3 commentary citations." That query is one CTE + AGE
   traversal + pgvector ANN + FTS. In a 3-store world it's an orchestration
   layer — and orchestration layers don't compose into products.
2. **An isnad-aware retrieval API.** This is the killer surface. Every RAG
   system doing Islamic content today retrieves by keyword or naive embedding.
   Yours retrieves by _chain credibility weighted by narrator graph centrality_.
   That's a defensible endpoint. Sell it. Or open-source it and own the
   category.
3. **Narrator-disambiguation as a service.** Tens of thousands of narrators with
   overlapping names is a known nightmare. With graph + vectors co-located, you
   can ship a public "resolve this narrator" endpoint that competitors literally
   cannot replicate without your stack.
4. **Provenance-traced LLM grounding.** Every answer cites the isnad path.
   That's the product feature Anthropic/OpenAI cannot offer on classical Arabic.
   Build the MCP server.
5. **Parallel-hadith discovery.** Vector + graph in one query surfaces
   undocumented cross-collection parallels. That's a publishable research
   contribution, not a feature.

**Skip SQLite. Skip Neo4j licensing tax. Skip Qdrant duplication.** Postgres
16 + pgvector + AGE on one box scales to your full corpus and gives you a single
backup, single migration story, single query plane. The constraint isn't
operational — it's _imaginative_. One store means you can ship the weird query
that becomes the product.

### The Outsider (Response A)

I have to be honest: I read this twice and the thing that kept jumping out at me
wasn't the database question. It was the gap between "today: 8 books, 1 sample
page, 30KB of JSON" and the elaborate four-database stack being proposed. Thirty
kilobytes. That fits in a single email. You're picking a five-engine setup for a
go-kart.

Let me ask the dumb questions:

**Who are these "millions of hadiths" for?** You said it yourself: "thousands
eventually" of books. "Millions" of hadiths. "Eventually." That word is doing a
lot of work. The classical hadith corpus across all major collections is roughly
50,000–100,000 unique narrations depending on how you count. Where are the
millions coming from? Translations? Variants? If so, that's not a million
distinct records, that's denormalization you're choosing. The real working set
might be 100k rows.

**Does a human user actually traverse 5 hops of narrator chains in your UI?**
Pattern 7 says "1-5 hops." I'd bet money that 95% of real user sessions never
click past hop 1 or 2. Is the 5-hop traversal a feature anyone has asked for, or
is it "well the data is a graph, so we should support graph queries"? Because
shortest-path-through-narrators is the kind of thing engineers find beautiful
and users never touch.

**Can you explain to your mother why this needs a graph database?** "I want to
look up who taught whom" is a SELECT with a JOIN. "I want to find every teacher
of a teacher of a teacher" is recursive — but it's still a tree, and Postgres
recursive CTEs eat trees for breakfast on a dataset this size.

**Vector search for "related hadiths" — has anyone clicked it yet?** You have
one sample page. Nobody has used this product. You're sizing infrastructure for
usage patterns that are hypothetical.

My outsider verdict: the suspicious word in this whole brief is "eventually."
You're not building for what exists; you're building for an imagined future.
Ship Postgres. One database. Add pgvector when a user actually complains that
related-hadith search is missing. Add a graph extension the day someone files a
real query that recursive CTEs can't answer. You will almost certainly never
reach that day, and that's fine.

The fewer-moving-parts culture is right. Trust it.

### The Executor (Response C)

Monday morning, here's what you do: nothing new. You keep shipping on JSON.

Let me be blunt about your actual situation. The upstream pipeline **has not
been run on the full corpus yet**. You don't have a Postgres dump. You don't
have a Neo4j export. You don't have Qdrant collections. You have a
`pyproject.toml` that lists ambitions. Picking a storage stack right now is
choosing furniture for a house that hasn't been built.

**The shortest path:** keep JSON until sol-next actually produces real output.
When it does, your first move is `docker compose up postgres` — one container,
one backup script (`pg_dump | zstd | rclone`), one thing to patch when a CVE
drops. That's it.

**On your four questions:**

1. **pgvector over Qdrant.** Until you have >10M vectors and measurable latency
   pain, a separate vector DB is a second daemon, a second backup story, a
   second upgrade cycle, and a second thing that goes down at 2am. pgvector with
   HNSW handles millions of rows fine on a single buildhost box. Postpone Qdrant
   until you can prove pgvector is the bottleneck.
2. **Recursive CTEs.** Not Neo4j. Not AGE. Not Memgraph. 1–5 hop narrator chains
   on tens of thousands of nodes is a `WITH RECURSIVE` query that runs in
   milliseconds with proper indexes. Neo4j means: JVM tuning, separate auth,
   separate backups, license anxiety on Enterprise features, and a CVE channel
   you now have to watch. AGE means running a Postgres extension that half the
   world has never deployed. If CTEs ever genuinely hurt — which they won't at
   your scale — you migrate then.
3. **One store: Postgres.** FTS via `tsvector` (Arabic dictionary or trigram
   fallback), vectors via pgvector, graph via CTEs, KV cache via `UNLOGGED`
   tables or skip Redis entirely until you see cache misses matter. Redis is the
   easiest one to bolt on later — it's a 30-second add.
4. **Skip SQLite.** Not because SQLite is bad — it's great — but pgvector and
   proper FTS push you to Postgres anyway. Don't migrate twice.

**Docker-compose: one service.** Backup: one cron. Upgrade path: one `apt`.
Ship.

---

## Peer reviews (with anonymization mapping revealed)

### Reviewer 1

**Strongest: Response D (First Principles).** The only response that actually
read the brief instead of pattern-matching on "graph + vector + multilingual."
It correctly identifies that sol-next2 is a _read-only artifact server_, not an
OLTP system — the pipeline already computed the joins. The collapse of 8 access
patterns into 3 primitives (key lookup, inverted index, vector ANN) is the kind
of reduction that prevents two years of wasted ops work. SQLite + FTS5 +
sqlite-vec + in-memory adjacency lists is technically correct _and_ matches the
single-dev self-hosted constraint.

**Biggest blind spot: Response E (Expansionist).** Selling a startup pitch, not
answering the question. The "first queryable graph-vector index of hadith"
framing assumes a product strategy the user didn't ask about. Hand-waves AGE's
planner immaturity (B nails) and Arabic FTS weakness (B also nails).

**All five missed: Reproducibility and the pipeline contract.** Nobody asked:
what schema/format does sol-next _actually emit_? If upstream writes Postgres
dumps + Neo4j exports + Qdrant snapshots, then sol-next2 inherits that contract.
Also missed: bilingual embedding model choice drives vector dimensionality,
index size, and whether pgvector is even viable.

### Reviewer 2

**Strongest: Response D.** The only response that interrogates the _shape_ of
the workload rather than accepting the framing. The build-artifact distribution
insight is correct and load-bearing. Isnad chains pre- materialized inside
hadith documents. Cross-references are reverse indexes. The "graph" is an
adjacency list that fits in RAM. A is a close second for puncturing the
"eventually" hand-wave, but D actually proposes the right architecture.

**Biggest blind spot: Response E.** A pitch deck, not an engineering answer.
Conflates "consolidation unlocks moves" with "I should pick the most ambitious
stack." AGE is operationally fragile (B is right) and E never addresses it.
Ignores that the pipeline hasn't run yet.

**All five missed: Arabic-specific data quality and tokenization as a product
concern, not a backend one.** What's the embedding model for classical Arabic
with tashkeel? How are narrator name variants (kunya/nasab/laqab) normalized
_before_ storage? That decision constrains every store choice downstream — and
it belongs to sol-next, not sol-next2.

### Reviewer 3

**Strongest: Response D.** The only response that actually read the problem
statement. The corpus is precomputed by an upstream pipeline, append-rarely,
single-dev, read-mostly — that's a build artifact, not a transactional system. D
correctly decomposes the 8 "access patterns" into 3 primitives and notices that
isnad chains are _already materialized paths inside each hadith document_. C is
close but still reaches for Postgres reflexively; D questions whether any server
is needed at all.

**Biggest blind spot: Response E.** Selling a vision, not solving the stated
problem. Conflates _what would be impressive to build_ with _what the user
asked_. "The constraint isn't operational — it's imaginative" is exactly
backwards for a single-dev self-hosted setup with 30KB of data and an unrun
pipeline.

**All five missed: The pipeline's output contract.** Every response argues about
the destination store; none ask what sol-next actually _emits_. The SSOT
question isn't "which DB" — it's **whether sol-next2's store is the SSOT or a
derived view of sol-next's outputs**. That determines everything else, including
whether Arabic FTS quality is solvable downstream or must be specified upstream.

### Reviewer 4

**Strongest: Response D.** The only response that interrogated the _shape_ of
the data instead of the _names_ of the access patterns. The insight that
narrator chains are pre-materialized paths inside documents (you read them, not
traverse them) reframes the entire problem. "Commentaries citing X" being a
reverse-index dict is correct and devastating to the graph-DB premise. The
build-artifact framing matches reality.

**Biggest blind spot: Response E.** Mistakes ambition for architecture. The
"compounding unlocks" are product features, not database requirements — every
one of them is implementable on D's or C's stack. And E waves at Apache AGE
while B has already correctly flagged it as a trap.

**All five missed: The embedding pipeline lifecycle.** Whoever picks the model
owns it forever — re-embedding millions of multilingual hadiths on a model swap
is a multi-day job nobody scoped. Also: Arabic-specific tokenization and
normalization as a cross-cutting concern (only B gestures at it). And **citation
stability**: hadith IDs across collections (Bukhari numbering schemes, Shamela
vs printed editions) is the real SSOT problem.

### Reviewer 5

**Strongest: Response D.** The only response that re-frames the problem instead
of accepting it. The corpus is precomputed upstream, append- rarely, read-mostly
— that is a build-artifact distribution problem. SQLite + FTS5 + sqlite-vec +
JSON1, opened read-only by FastAPI, matches the actual workload. C is close but
still reaches for Postgres reflexively.

**Biggest blind spot: Response E.** Ignores that nobody has used this product.
"Compounding," "MCP server," "research contribution," "isnad-aware RAG" — all
imagined value before a single user has clicked anything. E is building a
portfolio narrative, not a backend.

**All five missed: The upstream contract.** sol-next declares Postgres + Neo4j +
Qdrant + Redis as targets but hasn't run on the full corpus. None proposed: let
sol-next emit a canonical flat artifact (Parquet/SQLite/ JSONL) as the contract,
decoupling pipeline internals from serving. Also missed: Arabic-specific FTS
costing, and i18n routing for bilingual page content as a first-class concern.

---

## Chairman's verdict

### Where the Council Agrees

Four of five advisors (B, D, A, C) reject the four-store stack outright. The
convergence point: the proposed Postgres + Neo4j + Qdrant + Redis configuration
is operational overkill for a single-dev, self-hosted, read-mostly workload
against a corpus that doesn't yet exist in materialized form. Only E argues for
the complex stack, and E's argument is product-vision dressed as architecture.

Three independent lines of attack reach the same destination on graph storage: B
(AGE planner is broken), C (recursive CTEs are milliseconds at this scale), and
D (it isn't graph-shaped at query time — isnad chains are pre-materialized paths
inside each hadith document). Nobody defends Apache AGE on technical grounds.
Neo4j is treated as serious-but- disproportionate by everyone except E.

Vector store consensus is softer but real: defer until pattern 6 has a real user
(B, A), and when you need it, pgvector is sufficient until you can prove
otherwise (C). Only E commits to pgvector preemptively, and for the wrong reason
("hybrid SQL queries"). Qdrant has no organic advocates.

Every reviewer ranked D strongest. Every reviewer ranked E weakest. That's not
noise.

### Where the Council Clashes

**SQLite vs Postgres in production.** D says SQLite + FTS5 + sqlite-vec + JSON1
read-only is the correct architecture because the workload is artifact
distribution, not database serving. C says skip SQLite entirely because pgvector
and "proper FTS" push you to Postgres and you'd migrate twice. B dismisses
SQLite as "suicidal at thousands of books." The disagreement is real because
they're answering different questions: D is sizing for the actual workload
(read-only, single writer upstream), C and B are sizing for the workload they
expect to inherit.

**Arabic FTS in Postgres.** B is the only advisor who treats Arabic tokenization
as a first-class concern and concludes Postgres tsvector is inadequate without
significant custom work — recommending Meilisearch or OpenSearch. C, D, E
hand-wave this. Reviewers 2 and 4 caught the omission.

**Whether to plan for scale at all.** A and D say no — the working set is ~100k
rows, "eventually" is hypothetical, ship for what exists. C says ship Postgres
now because migration cost beats premature optimization. E says scale is the
entire point. A and D have the data on their side: 30KB today, an unrun pipeline
upstream, zero users.

### Blind Spots the Council Caught

Four of five reviewers independently flagged the same gap nobody in the advisor
pool addressed: **the upstream contract.** None of the five advisors asked what
sol-next actually emits. If sol-next writes Postgres dumps and Neo4j exports,
rejecting them means maintaining an ETL layer forever. If it emits Parquet or
JSONL, D's artifact model is trivial. The SSOT question isn't "which database" —
it's whether sol-next2's store is the SSOT or a derived view.

Two reviewers flagged **embedding pipeline lifecycle**: whoever picks the
multilingual classical-Arabic embedding model owns re-embedding millions of
records on every model swap. That decision belongs upstream, not in sol-next2.

Two reviewers flagged **Arabic-specific tokenization and narrator-name
normalization** (kunya/nasab/laqab variants) as a data-quality concern that
constrains every downstream store choice — and again, belongs to sol-next.

One reviewer flagged **citation stability** — Bukhari numbering schemes, Shamela
vs printed editions — as the real SSOT problem hiding behind the storage
question.

### The Recommendation

Adopt D's architecture, modified by the reviewer-caught blind spot.

**Concretely:** sol-next2 reads a single canonical artifact emitted by sol-next.
Default to SQLite with FTS5 + sqlite-vec + JSON1, opened read-only by FastAPI,
with NetworkX in-process for the rare narrator-traversal query. The artifact is
versioned, immutable, and atomically swapped on republish.

But first, **negotiate the upstream contract.** sol-next should emit one
canonical flat artifact (SQLite file or Parquet bundle) as the SSOT — not
Postgres/Neo4j/Qdrant snapshots. This decouples pipeline internals from serving
and resolves the SSOT question the council kept circling.

Two carve-outs from D's pure position:

1. If B is right about Arabic FTS quality (and the council didn't refute him),
   SQLite FTS5 with custom Arabic tokenizer needs validation against real
   queries before commitment. If it fails, add Meilisearch as a derived index —
   still rebuilt from the canonical artifact, not a second SSOT.
2. Keep Postgres as the _escape hatch_, not the default. The day a user
   complains about something SQLite + adjacency lists can't do, swap. Migration
   from a versioned read-only artifact to Postgres is a one-day job, not a
   rewrite.

C's instinct to "just ship Postgres" is the second-best answer and acceptable if
the team has zero appetite for the artifact model. E's stack is wrong for the
stated problem.

### The One Thing to Do First

Go to the sol-next pipeline and define its **output contract**: one versioned
canonical artifact (SQLite or Parquet) that sol-next2 consumes as immutable
input. Every storage decision downstream — FTS engine, vector index, graph
representation — becomes a derived-view problem instead of an SSOT problem. Do
this before writing a line of sol-next2 storage code.
