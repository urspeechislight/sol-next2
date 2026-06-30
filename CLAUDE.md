# Agent guidance — sol-next2

sol-next2 is a **knowledge graph reader** for classical Arabic manuscripts. It
consists of:

- `frontend/` — the live app: React 18 + TypeScript + Vite. Hash-based routing
  (`src/lib/routes.ts`), a token-driven design system under
  `src/lib/design-system/`, and a single typed API client in
  `src/lib/api/client.ts`. The Vite dev server binds all interfaces and proxies
  the `/api` prefix to the backend server-side, so a remote workstation reaches
  it via the host's address (no client-side `localhost` assumption).
- `src/backend/` — FastAPI service exposing the corpus (domains, books, TOC,
  pages, daily picks, rijal/canonical narrators, corpus + Qurʾān search) over a
  read-only `/api`. Backed by curated JSON in `data/` plus two read-only SQLite
  artifacts — `corpus.db` (FTS5) and `registry.db` — that sol-next2 builds
  itself from the `SOL_BOOKS_DIR` corpus root, and serves page text from that
  same root at request time.
- `.claude/` — agent guardrail harness mirrored from sol-next1, with sol-next's
  legacy `validate.sh` chained as a second PreToolUse layer.
- `lefthook.yml` — git-side mirror of the same rules at commit time.

`src/frontend/` is the superseded Babel-in-browser handoff prototype; it is not
served and not wired into the build. The live frontend is `frontend/`.

The NLP pipeline that would produce structured spans, hadith units, and narrator
links lives in the sibling project `sol-next/`. sol-next2 does **not** run it;
the reader currently serves raw page text until that structured data exists.

**Storage contract:** see
[`docs/adr/0001-storage-contract.md`](./docs/adr/0001-storage-contract.md).
TL;DR: sol-next2 is read-mostly and self-contained. It materializes its own
read-only SQLite artifacts (FTS5 today; `sqlite-vec` is the planned addition for
semantic search) from the `SOL_BOOKS_DIR` corpus root and serves them
read-only/immutable at runtime — no external database services, only stdlib
`sqlite3`.

---

## Required reading (in order)

1. Section "Data Integrity Is Non-Negotiable" below — inherited verbatim from
   sol-next/CLAUDE.md. These rules govern the backend.
2. Section "Rules summary" below — inherited from sol-next1/CLAUDE.md. The
   harness enforces them.
3. `frontend/src/app/App.tsx` and `frontend/src/lib/routes.ts` — the live app's
   root component and hash-routing SSOT. Read before touching the UI.
   (`src/frontend/` is the dead handoff prototype; ignore it.)

---

## Data Integrity Is Non-Negotiable

This is production software processing irreplaceable scholarly data. These rules
are absolute and override any other instinct toward convenience.

**Fail loudly. Always.** If a phase cannot produce correct output, it raises. It
does not return a plausible-looking wrong answer. A span that cannot be labeled
is not silently labeled `UNKNOWN` and passed forward. An unresolvable config
reference is not silently skipped. Fake output corrupts the knowledge graph in
ways that are invisible until a scholar trusts a wrong connection.

**No `except: pass`. No `except Exception: continue`.** Every exception must be
logged with full context (`logger.error(..., exc_info=True)`) and either
re-raised or converted to a typed error with `raise NewError(...) from e`.
Silent suppression of exceptions is forbidden without exception.

**No silent fallbacks.** If you find yourself writing `or []`, `or {}`,
`or "UNKNOWN"` in an error path, stop and ask: is this a legitimate empty state,
or am I hiding a bug? If you are hiding a bug, raise instead.

**Wrong is worse than absent.** The pipeline produces claims about manuscripts.
A wrong claim — a wrong behavior label, a spurious citation edge, an incorrect
narrator extraction — is actively harmful. When uncertain, produce nothing and
log why. Uncertainty is not a reason to invent.

---

## Rules summary (the harness will block violations)

**Design system (SSOT/DRY)**

- Colors, typography, spacing, radii, shadows, motion — defined ONLY in
  `frontend/src/lib/design-system/tokens.css`.
- No raw hex/rgb/hsl color literals outside `tokens.css`.
- No inline `style="..."` attributes in component files.

**Code quality**

- Files: warn ≥400 LOC, **block ≥450 LOC** — at 400 lines, split into
  submodules.
- Functions: block ≥80 LOC.
- No bare `except:` or `except X: pass` (`no_silent_except`).
- No magic numbers (literals other than `-1, 0, 1, 2, 100`); use named
  constants.
- All Python functions need type hints + docstrings.
- No `print` in non-script code; use `structlog`.
- Test names: `test_should_<verb>_<object>_<condition>`.

### SSOT / DRY — full taxonomy

Every kind of thing the codebase repeats has been classified. Items marked
**enforced** are checked by a hook and will block the tool call (or the commit).
Items marked **convention** are documented expectations agents should
self-check; the lefthook gate runs lint_staged.py over staged files so a future
enforcement upgrade lands automatically. Items marked **deferred** are honest
about what we couldn't enforce without high false-positive risk.

**Before you write a new function, class, or constant — search first.** The
enforced checks below are a backstop, not a substitute for reuse. The
SessionStart hook injects an inventory of public symbols under `src/` into
context — consult it, and `Grep` the codebase by _behaviour_ (not just name) for
an existing implementation before adding one. If something close exists, import
and extend it; if it genuinely must differ, say why. A duplicate the harness
then blocks (DRY-001 name, DRY-002 class, DRY-003 body) is a wasted round-trip
you can avoid by looking first.

| What                                                    | How                  | Rule                                                                                                                                                 |
| ------------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Module-level constants                                  | **enforced (block)** | `constant_sprawl` (SSOT-001): name AND value collisions across files                                                                                 |
| Magic numbers in `src/`                                 | **enforced (block)** | `magic_numbers` (QUAL-014): allowed bare `-1, 0, 1, 2, 100` only                                                                                     |
| Module-level functions                                  | **enforced (block)** | `function_duplication` (DRY-001 name): public-name collisions across files                                                                           |
| Module-level classes                                    | **enforced (block)** | `class_duplication` (DRY-002): covers DTOs, schemas, enums, exceptions, TypedDict, NamedTuple                                                        |
| Design tokens (color/space/radius/type)                 | **enforced (block)** | `no_raw_colors`, `no_arbitrary_values`, `no_inline_styles` — defined only in `frontend/src/lib/design-system/tokens.css`                             |
| Env var reads (`os.getenv`)                             | **enforced (block)** | `centralization` (CENTRAL-001): only in `src/backend/core/{config,settings}.py`                                                                      |
| Regex patterns (`re.compile/search/...`)                | **enforced (block)** | `centralization` (CENTRAL-002): only in `src/backend/**/patterns.py`                                                                                 |
| HTTP status codes (bare 200/404/500…)                   | **enforced (block)** | `centralization` (CENTRAL-003): use `status.HTTP_*` from `starlette.status`                                                                          |
| HTTP route decorators (`@router.get`/`@app.post`)       | **enforced (block)** | `centralization` (CENTRAL-004): only under `src/backend/api/`                                                                                        |
| Raw SQL strings                                         | **enforced (block)** | `centralization` (CENTRAL-005): only in `src/backend/repositories/` (read) or `src/backend/build/` (write) or migrations                             |
| Dependency manifests (pyproject/package.json/lockfiles) | **enforced (block)** | `single_pyproject` (BUILD-001): root-only; deploy files under `deploy/`                                                                              |
| Silent fallbacks (return None/[]/{}/UNKNOWN in except)  | **enforced (block)** | `fail_loud` (FAILFAST-001) + `no_silent_except` (QUAL-012)                                                                                           |
| Auth checks (`require_*`, `verify_token`)               | **enforced (block)** | `centralization` (CENTRAL-008): only in `src/backend/auth/`                                                                                          |
| JWT encode/decode                                       | **enforced (block)** | `centralization` (CENTRAL-009): only in `src/backend/auth/`                                                                                          |
| Password hashing (bcrypt/argon2)                        | **enforced (block)** | `centralization` (CENTRAL-010): only in `src/backend/security/`                                                                                      |
| Cache reads/writes                                      | **enforced (block)** | `centralization` (CENTRAL-011): only in `src/backend/cache/`                                                                                         |
| Metrics emission (`metrics.*`, statsd)                  | **enforced (block)** | `centralization` (CENTRAL-012): only in `src/backend/observability/`                                                                                 |
| Trace span creation                                     | **enforced (block)** | `centralization` (CENTRAL-013): only in `src/backend/observability/`                                                                                 |
| Cron expressions                                        | **enforced (block)** | `centralization` (CENTRAL-014): only in `src/backend/schedules.py`                                                                                   |
| UUID/ULID/token generation                              | **enforced (block)** | `centralization` (CENTRAL-015): only in `src/backend/core/ids.py`                                                                                    |
| Feature flag reads                                      | **enforced (block)** | `centralization` (CENTRAL-016): only in `src/backend/feature_flags.py`                                                                               |
| Health/liveness/readiness endpoints                     | **enforced (block)** | `centralization` (CENTRAL-017): only in `src/backend/main.py`                                                                                        |
| Secret-store path refs (`vault://`, ARN)                | **enforced (block)** | `centralization` (CENTRAL-018): only in settings module                                                                                              |
| Frontend route paths (string literals)                  | **enforced (block)** | `centralization` (CENTRAL-006): only in `frontend/src/lib/routes.ts`                                                                                 |
| Frontend `fetch(`/`axios.*`                             | **enforced (block)** | `centralization` (CENTRAL-007): only in `frontend/src/lib/api/`                                                                                      |
| Validation rules                                        | **convention**       | Validation logic lives in `src/backend/validators/` — routes call it, never inline                                                                   |
| File-path string literals                               | **convention**       | Define in `src/backend/core/paths.py`. (Auto-enforcement deferred — high FP risk on doc paths, test fixtures.)                                       |
| Date/time format strings (`"%Y-%m-%d"`)                 | **convention**       | Define in `src/backend/utils/time.py`; use ISO 8601 everywhere (`datetime.isoformat()`). Pydantic emits ISO 8601 by default — keep it.               |
| Repository pattern (DB access in one layer)             | **convention**       | All SQLAlchemy / asyncpg in `src/backend/repositories/`; services call repos, not the ORM. (`CENTRAL-005-sql` already blocks raw SQL outside repos.) |
| Email/notification/PDF templates                        | **convention**       | One templates dir: `src/backend/templates/{email,notification,pdf}/`. Layouts/footers/branding inherited via Jinja `extends`.                        |
| ADRs                                                    | **convention**       | All ADRs under `docs/adr/NNNN-title.md`. PR review enforces; `docs_location` rejects markdown outside `docs/` except root README/CLAUDE.             |
| Third-party API clients (one per vendor)                | **convention**       | `src/backend/integrations/<vendor>.py` — one Stripe client, one Twilio client, etc.                                                                  |
| Structured logging fields (`request_id`, `user_id`)     | **convention**       | Use `structlog.contextvars` middleware; never `f"... {request_id} ..."` in log lines.                                                                |
| Error messages (text of `raise X("...")`)               | **deferred**         | Semantic dedup is hard. PR review catches duplicate-message families.                                                                                |
| i18n / user-facing copy strings                         | **deferred**         | Cannot reliably distinguish copy from technical strings statically. When i18n becomes real, drive enforcement off the catalog.                       |
| Function bodies — exact copy (rename only)              | **enforced (block)** | `function_duplication` (DRY-003): identical AST body (ignoring name + leading docstring), ≥3 statements                                              |
| Function-body _similarity_ (copy-paste with variations) | **deferred**         | Fuzzy matching is fragile (false positives). DRY-003 catches only exact copies; variations need PR review + the rule of three.                       |
| Cross-stack constants (frontend ↔ backend)              | **deferred**         | Cross-language indexing is its own project. Share via OpenAPI codegen for values that must agree across stacks.                                      |
| Parallel `if/elif`/`switch` chains on the same enum     | **deferred**         | AST-level detection without semantic understanding is fragile. PR review.                                                                            |
| TS/JSX class & hook deduplication                       | **deferred**         | Requires TS AST. Will land once the frontend has a real build pipeline; PR review until then.                                                        |
| OpenAPI contract freshness (backend ↔ frontend)         | **deferred**         | Separate task: a hook that fails if `src/backend/api/` changes don't refresh `openapi.json` (or its codegen output).                                 |
| Tenant isolation, currency/money, sagas, A/B            | **N/A**              | sol-next2 is a single-tenant scholar tool; no currency, no event-sourcing, no experimentation.                                                       |
| IaC, K8s, service mesh, DNS, backups                    | **N/A (yet)**        | No infra deployed for sol-next2 yet. Re-evaluate when those land.                                                                                    |

**Imports / boundaries**

- Backend cannot import from frontend; frontend talks to backend via HTTP.

**Security**

- No secrets in code. Hooks scan for AWS/GCP keys, API tokens, private keys,
  `.env` patterns.
- No `eval`, `exec`, `__import__` of dynamic strings.
- No `os.system`, `subprocess.shell=True` in app code.

---

## Running checks locally

```bash
pnpm run ci         # everything (pnpm reserves bare `ci`, so `run` is required)
pnpm format:check   # prettier
pnpm py:check       # ruff + pyright
pnpm py:test        # backend tests
pnpm harness:test   # harness self-tests
```

Install the git hooks once:

```bash
pnpm install && pnpm exec lefthook install
```

## When the harness blocks you

Each block emits a structured message: `rule_id`, `why`, `how to fix`. Don't
bypass — read the linked doc and adjust. If you genuinely think the rule is
wrong, open a doc PR proposing the change; do not edit `.claude/policies/` to
wave yourself through.

## Adaptations from sol-next1

The harness was mirrored verbatim from sol-next1. These project-specific
adaptations were made:

- `lib/paths.py::is_design_token_file` accepts both
  `frontend/src/lib/design-system/tokens.css` (the live app) and
  `src/frontend/tokens.css` (the legacy handoff prototype).
- `pyproject.toml::packages` is `["src/backend"]` — sol-next2 has no pipeline
  package.
- The frontend has a real Vite + TypeScript toolchain (`fe:test`, `fe:build` in
  the root `package.json`; `vite`, `vitest`, `typescript` in `frontend/`).
  SvelteKit-only scripts (svelte-check) were never carried over — this is a
  React app, not Svelte.
- `.claude/settings.json` chains sol-next's legacy `validate.sh` at
  `.claude/hooks/sol-next-legacy/validate.sh` as a second PreToolUse hook on
  Write/Edit/MultiEdit/Bash — its 24 bash-implemented rules complement the
  Python dispatcher.
