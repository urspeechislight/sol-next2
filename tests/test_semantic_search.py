"""Tests for ``repositories.semantic``: plan parsing, merging, and the route contract.

The planner's network seam (``semantic._client``) and the engine seam
(``corpus_repo.search``) are replaced, never the functions under test — the
same swap-the-seam approach the corpus proxy tests use.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.core.errors import SemanticSearchError
from backend.core.settings import Settings
from backend.models.search import CorpusMatch
from backend.repositories import corpus as corpus_repo
from backend.repositories import semantic
from backend.repositories.semantic import SemanticPlan, parse_plan

# ---- parse_plan: the planner reply is untrusted input ----------------------


def _hit(urn: str, page: int) -> CorpusMatch:
    return CorpusMatch(
        urn=urn, title_ar="كتاب", category="sunni-hadith-general", page=page, snippet="نص"
    )


def test_should_keep_plan_order_dedupe_and_caps() -> None:
    plan = parse_plan(
        {
            "categories": ["sunni-hadith-general", "sunni-hadith-general", "shia-tafsir"],
            "queries": ["الطلاق", " الطلاق ", "النكاح", "نية الطلاق", "خطبته"],
        }
    )
    assert plan.categories == ("sunni-hadith-general", "shia-tafsir")
    assert plan.queries == ("الطلاق", "النكاح", "نية الطلاق", "خطبته")


def test_should_drop_unknown_slugs_and_keep_valid() -> None:
    plan = parse_plan({"categories": ["not-a-slug", "sunni-hadith-general"], "queries": ["الطلاق"]})
    assert plan.categories == ("sunni-hadith-general",)


def test_should_reject_plan_listing_only_unknown_slugs() -> None:
    with pytest.raises(SemanticSearchError, match="unknown category"):
        parse_plan({"categories": ["not-a-slug"], "queries": ["الطلاق"]})


def test_should_reject_plan_missing_all_queries() -> None:
    with pytest.raises(SemanticSearchError, match="no search phrases"):
        parse_plan({"categories": ["sunni-hadith-general"], "queries": []})


def test_should_drop_entries_lacking_string_type() -> None:
    plan = parse_plan({"categories": [7, "shia-tafsir"], "queries": ["الطلاق", 42, ""]})
    assert plan.categories == ("shia-tafsir",)
    assert plan.queries == ("الطلاق",)


# ---- _extract_json: tolerate fenced/prosed replies, nothing else -----------


def test_should_extract_json_despite_fences_and_prose() -> None:
    data = semantic._extract_json('Here you go:\n```json\n{"queries": ["x"]}\n```')
    assert data == {"queries": ["x"]}


def test_should_reject_reply_without_any_braces() -> None:
    with pytest.raises(SemanticSearchError, match="no JSON object"):
        semantic._extract_json("no plan here")


def test_should_reject_reply_with_invalid_json() -> None:
    with pytest.raises(SemanticSearchError, match="not valid JSON"):
        semantic._extract_json('{"queries": ["x",}')


# ---- plan cache: bounded TTL, keyed by the folded query --------------------


def test_should_replay_cached_plan_until_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(semantic, "_PLAN_CACHE", {})
    plan = SemanticPlan(categories=(), queries=("الطلاق",))
    semantic._cache_put("key", plan)
    assert semantic._cache_get("key") == plan
    # An expired entry is dropped on read, not served.
    semantic._PLAN_CACHE["old"] = (float("-inf"), plan)
    assert semantic._cache_get("old") is None
    assert "old" not in semantic._PLAN_CACHE


def test_should_evict_oldest_entry_past_size_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(semantic, "_PLAN_CACHE", {})
    monkeypatch.setattr(semantic, "SEMANTIC__PLAN_CACHE_SIZE", 2)
    semantic._cache_put("a", SemanticPlan((), ("a",)))
    semantic._cache_put("b", SemanticPlan((), ("b",)))
    semantic._cache_put("c", SemanticPlan((), ("c",)))
    assert set(semantic._PLAN_CACHE) == {"b", "c"}


# ---- search: plan -> parallel engine fan-out -> merged page ----------------


def _fake_engine(hits: dict[str, list[CorpusMatch]]):
    """An engine seam keyed by phrase: returns that phrase's hit list."""

    async def search(
        query: corpus_repo.SearchQuery,
        *,
        limit: int,
        offset: int,  # noqa: ARG001 — part of the engine signature being mocked
    ) -> tuple[list[CorpusMatch], int]:
        items = hits[query.q]
        return items[:limit], len(items)

    return search


def _plan_seam(plan: SemanticPlan):
    """A plan seam returning a fixed plan regardless of the query."""

    async def fake_plan(_q: str) -> SemanticPlan:
        return plan

    return fake_plan


async def test_should_merge_phrases_round_robin_with_dedupe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hits = {
        "الطلاق": [_hit("bookA", 1), _hit("bookA", 2), _hit("bookB", 5)],
        "النكاح": [_hit("bookA", 1), _hit("bookC", 9)],
    }
    engine = _fake_engine(hits)
    monkeypatch.setattr(
        semantic, "plan", _plan_seam(SemanticPlan(("sunni-hadith-general",), tuple(hits)))
    )
    monkeypatch.setattr(semantic.corpus_repo, "search", engine)

    items, total = await semantic.search_planned(
        "marriage with intent to divorce", limit=2, offset=0
    )
    # Rank-major round-robin: rank 0 of each phrase, then rank 1 — the best
    # wording's hits never crowd out the alternates'. bookA:1 repeats and is
    # deduped; total counts unique hits only.
    assert [(m.urn, m.page) for m in items] == [("bookA", 1), ("bookA", 2)]
    assert total == 4


async def test_should_slice_merged_window_for_paging(monkeypatch: pytest.MonkeyPatch) -> None:
    hits = {"الطلاق": [_hit("bookA", page) for page in range(1, 6)]}
    engine = _fake_engine(hits)
    monkeypatch.setattr(semantic, "plan", _plan_seam(SemanticPlan((), tuple(hits))))
    monkeypatch.setattr(semantic.corpus_repo, "search", engine)

    items, total = await semantic.search_planned("divorce", limit=2, offset=3)
    assert [(m.urn, m.page) for m in items] == [("bookA", 4), ("bookA", 5)]
    assert total == 5


# ---- route contract: blank query 422, unconfigured planner 503 --------------


def test_should_reject_route_query_when_blank(client: TestClient) -> None:
    response = client.get("/api/search/semantic?q=%20%20")
    assert response.status_code == 422


def test_should_answer_503_when_planner_unconfigured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "backend.repositories.semantic.get_settings",
        lambda: Settings(books_dir=Path("/tmp"), llm_api_key=""),
    )
    response = client.get("/api/search/semantic", params={"q": "divorce in sunni sources"})
    assert response.status_code == 503
    assert "SOL_LLM_API_KEY" in response.json()["detail"]
