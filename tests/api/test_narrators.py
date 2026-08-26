"""Tests for ``GET /api/narrators`` (paginated + filtered), ``/{id}``, and ``/{id}/graph``.

These run against the real ``data/registry.db`` artifact built by
``scripts/build_registry.py`` from sol-next3's narrator store, so the
assertions use comfortable floors rather than exact counts.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.patterns import normalize_narrator_name

NARRATOR_MIN_TOTAL = 89_000
SAMPLE_LIMIT = 5
KNOWN_ID = 3596438
UNKNOWN_ID = 99_999_999
HUB_ID = 3672621
SMALL_STUDENT_ROOT = 3596788
TEACHER_ROOT = 3596453
SUFYAN = "سفيان"
QUERY_FOLDED = normalize_narrator_name(SUFYAN)


def test_should_return_paginated_envelope_when_listing(client: TestClient) -> None:
    """`/api/narrators` returns {items, total, limit, offset}."""
    response = client.get("/api/narrators")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"items", "total", "limit", "offset"}


def test_should_load_the_full_corpus(client: TestClient) -> None:
    """The artifact carries the whole narrator store; assert a comfortable floor."""
    assert client.get("/api/narrators").json()["total"] >= NARRATOR_MIN_TOTAL


def test_should_respect_limit_parameter(client: TestClient) -> None:
    """`?limit=N` caps items at N."""
    payload = client.get("/api/narrators", params={"limit": SAMPLE_LIMIT}).json()
    assert len(payload["items"]) == SAMPLE_LIMIT
    assert payload["limit"] == SAMPLE_LIMIT


def test_should_filter_by_category_when_given(client: TestClient) -> None:
    """`?category=long_entry` narrows every row to that category."""
    payload = client.get(
        "/api/narrators", params={"category": "long_entry", "limit": SAMPLE_LIMIT}
    ).json()
    assert payload["total"] >= 1
    assert all(item["category"] == "long_entry" for item in payload["items"])


def test_should_filter_by_tradition_when_given(client: TestClient) -> None:
    """`?tradition=imami` narrows every row to that tradition."""
    payload = client.get("/api/narrators", params={"tradition": "imami", "limit": 24}).json()
    assert payload["total"] >= 1
    assert all(item["tradition"] == "imami" for item in payload["items"])


def test_should_narrow_total_on_query_substring(client: TestClient) -> None:
    """A name substring query returns a strict, non-empty subset of the corpus."""
    base = client.get("/api/narrators").json()["total"]
    narrowed = client.get("/api/narrators", params={"q": SUFYAN}).json()["total"]
    assert 0 < narrowed < base


def test_should_match_every_hit_on_query_substring(client: TestClient) -> None:
    """Every q= hit carries the substring in a folded alias or its primary name."""
    payload = client.get("/api/narrators", params={"q": SUFYAN, "limit": 24}).json()
    assert payload["items"]
    for item in payload["items"]:
        if SUFYAN in item["primary_name_ar"]:
            continue
        detail = client.get(f"/api/narrators/{item['id']}").json()
        assert any(
            QUERY_FOLDED in normalize_narrator_name(alias["name_ar"]) for alias in detail["aliases"]
        ), f"{item['id']} matched q= without any matching name"


def test_should_return_detail_when_id_known(client: TestClient) -> None:
    """A known id returns the full narrator record with claim sections."""
    response = client.get(f"/api/narrators/{KNOWN_ID}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == KNOWN_ID
    assert payload["primary_name_ar"]
    for key in ("aliases", "grades", "stances", "tarjama"):
        assert key in payload


def test_should_return_404_when_id_unknown(client: TestClient) -> None:
    """An out-of-range id yields a 404 naming the identifier."""
    response = client.get(f"/api/narrators/{UNKNOWN_ID}")
    assert response.status_code == 404
    assert str(UNKNOWN_ID) in response.json()["detail"]


def test_should_expand_students_graph(client: TestClient) -> None:
    """The students graph returns the root plus its student descendants."""
    response = client.get(f"/api/narrators/{SMALL_STUDENT_ROOT}/graph")
    assert response.status_code == 200
    payload = response.json()
    assert payload["root_id"] == SMALL_STUDENT_ROOT
    assert payload["direction"] == "students"
    assert payload["depth"] == 1
    assert len(payload["nodes"]) > 1
    assert payload["nodes"][0]["depth"] == 0
    assert payload["nodes"][0]["id"] == SMALL_STUDENT_ROOT
    assert payload["edges"]
    assert all(edge["source_label"] for edge in payload["edges"])
    assert not payload["truncated"]
    depths = {node["id"]: node["depth"] for node in payload["nodes"]}
    assert all(depths[edge["from_id"]] == depths[edge["to_id"]] - 1 for edge in payload["edges"])


def test_should_flag_truncation_on_hub_narrator(client: TestClient) -> None:
    """A hub narrator at depth 3 exceeds the node cap and reports truncated."""
    response = client.get(
        f"/api/narrators/{HUB_ID}/graph", params={"direction": "students", "depth": 3}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["truncated"] is True
    assert len(payload["nodes"]) <= 400
    assert all(node["depth"] <= 3 for node in payload["nodes"])


def test_should_reject_out_of_band_depth(client: TestClient) -> None:
    """depth is clamped by validation to the 1..3 band."""
    too_deep = client.get(f"/api/narrators/{SMALL_STUDENT_ROOT}/graph", params={"depth": 4})
    too_shallow = client.get(f"/api/narrators/{SMALL_STUDENT_ROOT}/graph", params={"depth": 0})
    assert too_deep.status_code == 422
    assert too_shallow.status_code == 422


def test_should_expand_teachers_graph(client: TestClient) -> None:
    """The teachers direction walks from_id ancestors of the root.

    In the teachers direction an edge points teacher→student as stored, so an
    ancestor's edge points AT a shallower node: from_id is one hop DEEPER than
    to_id along the rootward direction.
    """
    response = client.get(
        f"/api/narrators/{TEACHER_ROOT}/graph", params={"direction": "teachers", "depth": 2}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["direction"] == "teachers"
    assert len(payload["nodes"]) > 1
    assert payload["nodes"][0]["id"] == TEACHER_ROOT
    assert payload["nodes"][0]["depth"] == 0
    depths = {node["id"]: node["depth"] for node in payload["nodes"]}
    assert all(depths[edge["from_id"]] == depths[edge["to_id"]] + 1 for edge in payload["edges"])
