# ADR-0003: LLM-planned semantic search

Date: 2026-08-25
Status: Accepted
Extends: ADR-0001 (search stays a proxied external concern), CENTRAL-005 (one
corpus search engine)

## Context

Keyword search demands the vocabulary the corpus is written in. A reader who
knows the mas'ala in English ("marriage with the intention of divorce in
Sunni sources") but not its Arabic technical terms (نية الطلاق، يتزوج على
الطلاق) cannot reach the passages. The corpus engine is phrase-based and
excellent once given the right phrase and scope; the missing piece is the
English question → (scope, Arabic phrases) mapping.

## Decision

The LLM is a **planner, never a content source**. `GET /api/search/semantic`
sends the freeform question to an external LLM (Anthropic-messages protocol;
endpoint, model, and key all env-driven via `SOL_LLM_*` in
`core/settings.py`) together with the taxonomy SSOT, and requires strict
JSON: `{categories, queries}`. The plan is validated (slugs against
`_taxonomy`, phrases capped) and executed by the one corpus search engine
(`repositories.corpus`, broad mode, parallel per phrase, merged round-robin
and deduped by (urn, page)).

Consequences, chosen deliberately:

- **One result shape.** The route serves `Page[CorpusMatch]` — the corpus
  search's own envelope. A semantic hit and a keyword hit are the same object
  by construction; the frontend renders it through the same rows. No LLM text
  ever reaches the browser.
- **Content is sourced by titan end-to-end.** Snippets come from the engine's
  index; the LLM sees only the taxonomy and the question.
- **Failure is loud.** Missing `SOL_LLM_API_KEY` → 503 naming the setting;
  planner transport/contract failures → 502 (`SemanticSearchError`, mapped in
  `main.py`). Hallucinated slugs are dropped as untrusted input, but a plan
  that validates to nothing usable is a 502, never a silent empty page.
- **Plans are cached** per folded query (bounded TTL cache in
  `repositories/semantic.py`), so repeat questions pay the planner latency once.
- **Prompt inputs come from the SSOT.** The category catalog in the planner
  prompt is rendered from `_taxonomy.DOMAINS` at process start; a taxonomy
  edit re-plans without a code change.

## Non-goals

No vector/embedding index, no RAG answer synthesis, no per-result LLM
re-ranking. If retrieval quality ever demands embeddings, that is a new
engine concern behind the same `/search` proxy seam and a new ADR.
