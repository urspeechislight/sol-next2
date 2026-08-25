"""LLM-planned semantic search: freeform query in, corpus matches out.

The planner (an external LLM) never supplies content. It maps a freeform
question — usually English — onto the corpus's own retrieval vocabulary:
category slugs from the taxonomy SSOT and short Arabic full-text phrases.
The plan then executes through the one corpus search engine
(``repositories.corpus``), so hits, snippets, and the ``Page[CorpusMatch]``
envelope are identical to a keyword search by construction; there is no
second result shape to drift.

Failure contract (fail loud, never silent):

* missing ``SOL_LLM_API_KEY`` -> ``SemanticNotConfiguredError`` (503);
* planner unreachable, non-JSON, or out of contract -> ``SemanticSearchError``
  (502);
* hallucinated category slugs are dropped (untrusted input, validated against
  ``_taxonomy``), but a plan that named only unknown slugs, or that yields no
  usable phrase, is out of contract -> ``SemanticSearchError``.

Plans are cached per folded query: the planner is deterministic enough that a
re-run of the same question should not pay its latency twice, and the cache
key reuses ``fold_search`` so query identity matches the engine's own.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Final

import httpx

from backend.core.constants import (
    CORPUS__BACKEND_PAGE_LIMIT,
    HTTP__LLM_TIMEOUT_SECONDS,
    SEMANTIC__MAX_BOOKS,
    SEMANTIC__MAX_CATEGORIES,
    SEMANTIC__MAX_QUERIES,
    SEMANTIC__PLAN_CACHE_SIZE,
    SEMANTIC__PLAN_CACHE_TTL_SECONDS,
    SEMANTIC__PLANNER_MAX_TOKENS,
)
from backend.core.errors import SemanticNotConfiguredError, SemanticSearchError
from backend.core.settings import get_settings
from backend.models.search import CorpusMatch
from backend.patterns import fold_search
from backend.repositories import _taxonomy
from backend.repositories import books as books_repo
from backend.repositories import corpus as corpus_repo

_PLANNER_SYSTEM: Final[str] = """You are the retrieval planner for a digital library of \
classical Arabic manuscripts (hadith, fiqh, tafsir, narrators, history, adab). You never \
answer the question and never supply content: you translate the user's freeform request \
into a search plan the library's full-text engine can execute.

Respond with STRICT JSON only — no prose, no markdown fences:
{"categories": ["<slug>", ...], "queries": ["<Arabic phrase>", ...], "books": ["<work title>", ...]}

Rules:
- "categories": 0-6 slugs copied EXACTLY from the list below, matching the corpus the \
question asks about. If the question names a tradition ("Sunni sources", "Shia tafsir"), \
pick only categories of that tradition. Omit entirely when the question has no scope.
- "queries": 1-4 SHORT Arabic search phrases (1-5 words each) a scholar would search \
for, using classical technical terminology of the relevant discipline (e.g. fiqh mas'il \
vocabulary), not a translation of the question. Each phrase is a different wording or \
synonym; the engine matches them as partial phrase windows and folds diacritics.
- The FIRST phrase is the recall anchor: the question's single core term, one word, \
with the definite article when natural (e.g. "الطلاق", "الخيار", "العتق", "الجهاد"). \
The engine matches it anywhere in scope, so the plan can never come back empty. \
Phrases 2-4 then narrow with precise classical constructions — but verify their \
wording is how books actually head the discussion, not your own paraphrase.
- "books": 0-4 work titles the question explicitly names ("in Sahih al-Bukhari", "per \
Muslim") — copy the work's common name as the catalogue would spell it. Omit entirely when \
the question names no specific work.
- If the question is vague, plan for its most likely scholarly reading."""


@dataclass(frozen=True)
class SemanticPlan:
    """A validated retrieval plan: taxonomy slugs + Arabic FTS phrases."""

    categories: tuple[str, ...]
    queries: tuple[str, ...]
    books: tuple[str, ...]


@lru_cache(maxsize=1)
def _taxonomy_catalog() -> str:
    """Render the taxonomy as the planner's category list, once per process.

    Derived from ``_taxonomy.DOMAINS`` (the SSOT) so a taxonomy edit re-plans
    without a code change; per-category work counts are omitted to keep the
    prompt small and stable.
    """
    lines: list[str] = []
    for domain in _taxonomy.DOMAINS:
        lines.append(f"{domain.label}:")
        lines.extend(
            f"  - {category.slug} — {category.label} ({category.tradition})"
            for category in domain.categories
        )
    return "\n".join(lines)


def _extract_json(text: str) -> dict[str, Any]:
    """Pull the JSON object out of the planner's reply, rejecting the rest.

    The planner is instructed to answer with bare JSON, but the reply is
    untrusted input: tolerate surrounding fences or prose by taking the
    outermost brace span, then require an object.
    """
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise SemanticSearchError("LLM planner reply contains no JSON object")
    try:
        data = json.loads(text[start : end + 1])
    except ValueError as exc:
        raise SemanticSearchError(f"LLM planner reply is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SemanticSearchError("LLM planner reply is not a JSON object")
    return data


def _string_list(data: dict[str, Any], key: str) -> tuple[bool, list[str]]:
    """Read one plan field as a deduped string list + whether it was present.

    The presence flag lets the caller distinguish "planner named no scope"
    (legitimate) from "planner named only unknown slugs" (out of contract).
    Non-string or non-list entries are untrusted input and dropped.
    """
    raw = data.get(key)
    if raw is None:
        return False, []
    if not isinstance(raw, list):
        return True, []
    seen: set[str] = set()
    values: list[str] = []
    for entry in raw:
        if not isinstance(entry, str):
            continue
        value = entry.strip()
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return True, values


def parse_plan(data: dict[str, Any]) -> SemanticPlan:
    """Validate a planner reply into a ``SemanticPlan``.

    Slugs are checked against the taxonomy and unknowns dropped; phrases are
    kept as-is (the engine folds them). A reply that named categories but
    none valid, or that offers no usable phrase, is out of contract.
    """
    categories_raw, categories = _string_list(data, "categories")
    known = [slug for slug in categories if _taxonomy.is_known_category(slug)]
    if categories_raw and not known:
        raise SemanticSearchError("LLM planner named only unknown category slugs")
    _, raw_queries = _string_list(data, "queries")
    if not raw_queries:
        raise SemanticSearchError("LLM planner produced no search phrases")
    _, raw_books = _string_list(data, "books")
    resolved_books = books_repo.resolve_work_titles(raw_books[:SEMANTIC__MAX_BOOKS])
    return SemanticPlan(
        categories=tuple(known[:SEMANTIC__MAX_CATEGORIES]),
        queries=tuple(raw_queries[:SEMANTIC__MAX_QUERIES]),
        books=tuple(resolved_books[:SEMANTIC__MAX_BOOKS]),
    )


_PLAN_CACHE: dict[str, tuple[float, SemanticPlan]] = {}


def _cache_get(key: str) -> SemanticPlan | None:
    """Return a live cached plan for ``key``, dropping expired entries.

    The cache is a bounded, process-local map of folded query to
    ``(expires_at, plan)``.
    """
    entry = _PLAN_CACHE.get(key)
    if entry is None:
        return None
    expires_at, plan = entry
    if expires_at < time.monotonic():
        del _PLAN_CACHE[key]
        return None
    return plan


def _cache_put(key: str, plan: SemanticPlan) -> None:
    """Store a plan, evicting expired then oldest entries past the size cap."""
    if len(_PLAN_CACHE) >= SEMANTIC__PLAN_CACHE_SIZE:
        now = time.monotonic()
        for stale in [k for k, (at, _) in _PLAN_CACHE.items() if at < now]:
            del _PLAN_CACHE[stale]
        while len(_PLAN_CACHE) >= SEMANTIC__PLAN_CACHE_SIZE:
            del _PLAN_CACHE[next(iter(_PLAN_CACHE))]
    _PLAN_CACHE[key] = (time.monotonic() + SEMANTIC__PLAN_CACHE_TTL_SECONDS, plan)


@lru_cache(maxsize=1)
def _client() -> httpx.AsyncClient:
    """The process-wide async client bound to the planner base URL (pooled)."""
    return httpx.AsyncClient(
        base_url=get_settings().llm_base_url, timeout=HTTP__LLM_TIMEOUT_SECONDS
    )


async def _post_plan(q: str) -> dict[str, Any]:
    """One planner round-trip: the question in, a JSON reply object out.

    The single network seam; tests replace ``_client``. Any transport or
    contract failure surfaces as ``SemanticSearchError`` — a planner outage
    must be visible, never masked as "no results".
    """
    settings = get_settings()
    if not settings.llm_api_key:
        raise SemanticNotConfiguredError("LLM search is not configured: set SOL_LLM_API_KEY")
    payload = {
        "model": settings.llm_model,
        "max_tokens": SEMANTIC__PLANNER_MAX_TOKENS,
        "system": f"{_PLANNER_SYSTEM}\n\nCategory list:\n{_taxonomy_catalog()}",
        "messages": [{"role": "user", "content": q}],
    }
    headers = {
        "x-api-key": settings.llm_api_key,
        "anthropic-version": "2023-06-01",
    }
    try:
        response = await _client().post("/v1/messages", json=payload, headers=headers)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SemanticSearchError(f"LLM planner request failed: {exc}") from exc
    try:
        body = response.json()
    except ValueError as exc:
        raise SemanticSearchError(f"LLM planner returned non-JSON: {exc}") from exc
    try:
        text = "".join(block["text"] for block in body["content"] if block.get("type") == "text")
    except (KeyError, TypeError, AttributeError) as exc:
        raise SemanticSearchError(f"LLM planner reply outside contract: {exc}") from exc
    return _extract_json(text)


async def plan(q: str) -> SemanticPlan:
    """Plan the retrieval for ``q``, via the cache when it holds a live entry.

    The cache key case-folds the folded query, so "Marriage…" and "marriage…"
    share one plan instead of paying the planner twice and drifting apart.
    """
    key = fold_search(q).lower()
    if not key:
        raise SemanticSearchError("empty query")
    cached = _cache_get(key)
    if cached is not None:
        return cached
    parsed = parse_plan(await _post_plan(q))
    _cache_put(key, parsed)
    return parsed


async def search_planned(
    q: str,
    limit: int,
    offset: int,
    categories: tuple[str, ...] = (),
    book: str = "",
) -> tuple[list[CorpusMatch], int]:
    """Plan ``q`` and execute it on the corpus engine; return (slice, total).

    Each phrase runs as its own broad-mode engine query over the plan's
    categories (one round of ``asyncio.gather``), fetched to the engine's max
    page so the merged window is deep enough to page honestly. A plan that
    named works restricts every query to those books (phrase x book fan-out,
    the engine's single-title ``book`` filter); caller filters (a facet
    category click, a book drill-in) intersect the plan the same way. Hits
    merge round-robin across phrases (no single wording dominates), dedupe by
    (urn, page), and slice to the requested page. Every hit — snippet included
    — comes from the corpus engine, so the content path is titan end-to-end.
    """
    semantic_plan = await plan(q)
    categories = tuple(dict.fromkeys((*semantic_plan.categories, *categories)))
    books = (book,) if book else semantic_plan.books
    outcomes = await asyncio.gather(
        *(
            corpus_repo.search(
                corpus_repo.SearchQuery(q=phrase, mode="broad", categories=categories, book=title),
                limit=CORPUS__BACKEND_PAGE_LIMIT,
                offset=0,
            )
            for phrase in semantic_plan.queries
            for title in (books or ("",))
        )
    )
    merged: list[CorpusMatch] = []
    seen: set[tuple[str, int]] = set()
    streams = [items for items, _ in outcomes]
    for rank in range(max(len(items) for items in streams)):
        for items in streams:
            if rank >= len(items):
                continue
            hit = items[rank]
            key = (hit.urn, hit.page)
            if key in seen:
                continue
            seen.add(key)
            merged.append(hit)
    return merged[offset : offset + limit], len(merged)


async def planned_facets(
    q: str,
    categories: tuple[str, ...] = (),
    book: str = "",
) -> corpus_repo.SearchFacets:
    """Drill-down facets for the executed plan: same streams, same merge.

    Each (phrase, book) stream's facet scan is fetched (the engine counts a
    whole match-set per scan, independent of paging) and summed per key —
    categories first, books within the merged scope — mirroring how
    ``search_planned`` merges the streams, so the facet counts and the result
    rows can never disagree about the match-set they describe.
    """
    semantic_plan = await plan(q)
    scope_categories = tuple(dict.fromkeys((*semantic_plan.categories, *categories)))
    book_filter = (book,) if book else semantic_plan.books
    outcomes = await asyncio.gather(
        *(
            corpus_repo.facets(q=phrase, mode="broad", categories=scope_categories)
            for phrase in semantic_plan.queries
        )
    )
    plan_set = set(book_filter) if book_filter else None
    per_book: dict[str, int] = {}
    titles: dict[str, str | None] = {}
    for facets_result in outcomes:
        for facet in facets_result.books:
            if plan_set is not None and facet.title not in plan_set:
                continue
            per_book[facet.title] = per_book.get(facet.title, 0) + facet.count
            titles[facet.title] = facet.title_en
    category_of = books_repo.categories_of_titles(list(per_book))
    per_category: dict[str, int] = {}
    for title, count in per_book.items():
        slug = category_of.get(title)
        if slug is not None:
            per_category[slug] = per_category.get(slug, 0) + count
    return corpus_repo.SearchFacets(
        categories=[
            corpus_repo.CategoryFacet(slug=slug, count=count)
            for slug, count in sorted(per_category.items(), key=lambda kv: -kv[1])
        ],
        books=[
            corpus_repo.BookFacet(title=title, title_en=titles[title], count=count)
            for title, count in sorted(per_book.items(), key=lambda kv: -kv[1])
        ],
        volumes=[],
    )
