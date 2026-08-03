# ADR-0002: The absorbed producer role, the artifact seam, and the rule split

Date: 2026-07-02
Status: Accepted, with a noted divergence (2026-07-03) — see update below.
Supersedes: extends ADR-0001 (storage contract)

> **Update (2026-07-03).** `data/citations.db` (the Qurʾān-citation sidecar
> served by `src/backend/repositories/citations.py`) is a second producer:
> it's built by a one-off script living outside this repo
> (`~/sol-quran-citation-audit-20260703/build_sidecar.py`), not by
> `backend/build/`. The "one seam, both directions" decision below still holds
> for the pipeline ↔ serving boundary; it does not yet account for externally
> produced sidecar artifacts dropped into `data/`. Revisit if a second such
> sidecar appears — that's the signal to fold sidecar production into
> `backend/build/` or write a formal artifact-import contract.

## Context

ADR-0001 decided that sol-next2 consumes a single read-only SQLite artifact
and assumed the upstream sol-next pipeline would produce it. That is not how
the code evolved: sol-next2 ported the segment and extract phases itself
(M1 through M4) and now builds its own artifacts. The seam ADR-0001
prescribed exists, but the producer lives in this repository.

Separately, the original agent-harness enforced hard file-size, function-size,
and parameter-count caps as blocking rules. A 2026-07-01 audit found those
caps had manufactured structure instead of preventing it: a 14-line facade
module re-exporting two single-importer shards, five module families split at
arbitrary line counts, and transfer dataclasses whose only purpose was to
carry the same arguments across the seams the caps created.

## Decision

**One seam, both directions.** The only thing crossing between the pipeline
and the serving layer is a versioned SQLite artifact plus the small shared
vocabulary in `core.constants` (PERSON and the three unit types the
manuscript repository projects into reader DTOs). Serving code (`api/`,
`repositories/`, `main.py`) never imports `backend.pipeline`; the pipeline
never imports serving modules. Pipeline-only errors live in
`pipeline/errors.py` and pipeline-only vocabulary in `pipeline/vocab.py`.

**Build is a first-class layer.** `backend/build/runner.py` owns the artifact
lifecycle (wipe-and-create, the catalog build loop, batch commits, opt-in
ANALYZE/VACUUM, one CLI shell); each artifact module owns only its schema,
INSERT statements, and row projections. Scripts under `scripts/` are thin
drivers.

**Config is code except where it is data.** `config/sol.yaml` carries only
sections a ported phase reads (patterns, behaviors, atomicizers, extractors,
thresholds, toc_sections, failure_budget, narrative_genres,
cross_page_repair, narrator_extraction). Numeric thresholds are a typed
frozen dataclass: a misspelled name is a type error, a missing key a
load-time ConfigError. A deleted section returns together with the phase
that consumes it; git history is the parking lot.

**Invariant rules block; structure rules advise.** Fail-loud rules (no
silent fallbacks, no bare except, SSOT homes for regex/SQL/env/routes,
naming invariants) stay blocking. Size and shape signals (file LOC QUAL-010,
function LOC QUAL-011, parameter count FUNC-002) are advisories: they mark
redesign candidates for a human judgment, because as blocks they produced
exactly the facades, shards, and transfer bags they were meant to prevent.

**Refactors prove themselves against captured behavior.**
`scripts/capture_gates.py` snapshots the OpenAPI schema, seventeen golden
endpoint responses, and order-independent per-table content hashes of
`manuscript.db` into `~/sol-next2-rebuild-gates/`. A refactor lands only
when its rebuild hashes and API captures match the baseline. This gate has
already caught a corruption that typing, linting, and the full unit-test
suite all missed (a bidi-scrambled Arabic character class).

## Consequences

- The pipeline can be reshaped freely; identical artifact hashes are the
  proof of behavior preservation, not code review alone.
- Arabic combining-mark character classes must be codepoint-built
  (`*range(0x...)`), never retyped as literals: bidirectional rendering
  silently reorders them, and only the artifact gate catches the damage.
- Future phases (rijal, biography, theme, NER, enrich, graph) each bring
  back their own config sections, contracts, vocabulary, degraded modes,
  and extractor registrations when they land; nothing anticipatory is kept.
- When the artifact schema must change, the golden baselines are
  re-captured deliberately in the same commit, making contract changes
  visible in review rather than accidental.
