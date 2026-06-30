# sol-next2

Knowledge-graph reader for classical Arabic manuscripts.

- `frontend/` — the live app: React 18 + TypeScript + Vite, with a token-driven
  design system and a single typed API client.
- `src/backend/` — FastAPI service exposing the corpus (domains, books, TOC,
  pages, daily picks, narrators, search) over a read-only `/api`. Backed by
  curated JSON in `data/` plus two read-only SQLite artifacts (`corpus.db`,
  `registry.db`) that sol-next2 builds from the corpus root.
- `.claude/` — agent guardrail harness (see [`CLAUDE.md`](./CLAUDE.md)).
- `lefthook.yml` — git-side mirror of the same rules at commit time.

`src/frontend/` is the superseded Babel handoff prototype; it is not served. The
structured-data NLP pipeline lives in the sibling `sol-next/` project and is not
run here — the reader serves raw page text until that data exists.

## Prerequisites

The backend reads the manuscript corpus from a root directory of frontmatter
JSON files (the same tree `sol-next` consumes). Set `SOL_BOOKS_DIR` to its path.

## Quickstart

```bash
uv sync --group dev            # Python deps
pnpm install                   # Node deps
pnpm exec lefthook install     # git hooks (once)
```

Build the read-only SQLite artifacts from the corpus root (once, or when the
corpus changes):

```bash
SOL_BOOKS_DIR=/path/to/corpus/books uv run python scripts/ingest_books.py
SOL_BOOKS_DIR=/path/to/corpus/books uv run python scripts/build_corpus_index.py
uv run python scripts/build_registry.py
```

Run the two services on the host that owns the corpus:

```bash
# Terminal 1 — backend on :8001
SOL_BOOKS_DIR=/path/to/corpus/books uv run uvicorn backend.main:app --port 8001

# Terminal 2 — Vite dev server (binds all interfaces)
pnpm --filter @sol-next2/frontend dev
```

The Vite dev server binds all interfaces and proxies the `/api` prefix to the
backend **server-side**. From a remote workstation, open the URL Vite prints for
the host (for example `http://<host>:5173/`) — the browser never reaches the
backend directly, so no client-side `localhost` or CORS setup is needed.

```bash
pnpm ci                       # format / lint / type-check / test (the gate)
```

See [`CLAUDE.md`](./CLAUDE.md) for the data-integrity and harness rules every
contributor (human and agent) must follow.
