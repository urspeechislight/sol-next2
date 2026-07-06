"""Tests for the Qurʾān API: verse lookup by reference, and verse search by term."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_should_resolve_verse_when_reference_valid(client: TestClient) -> None:
    """68:4 resolves to its pointed + bare text and the surah's ayah count."""
    payload = client.get("/api/quran/68/4").json()
    assert payload["surah"] == 68
    assert payload["ayah"] == 4
    assert payload["verse_count"] == 52  # al-Qalam has 52 ayat
    assert "خُلُق" in payload["text_ar"]  # diacritized form
    assert payload["text_plain"] == "وإنك لعلى خلق عظيم"  # bare form, letters intact


def test_should_resolve_full_surah_in_order(client: TestClient) -> None:
    """A surah returns every numbered ayah in recitation order."""
    payload = client.get("/api/quran/1").json()
    assert payload["surah"] == 1
    assert payload["verse_count"] == 7
    assert [v["ayah"] for v in payload["verses"]] == list(range(1, 8))
    assert all(v["text_ar"] for v in payload["verses"])


def test_should_reject_full_surah_when_out_of_range(client: TestClient) -> None:
    """A surah beyond 114 is not found rather than an empty run."""
    assert client.get("/api/quran/200").status_code == 404


def test_should_strip_marks_keeping_letters_when_plain_form(client: TestClient) -> None:
    """text_plain drops vowel marks but preserves hamza/alef letters."""
    payload = client.get("/api/quran/2/255").json()
    assert "ُ" not in payload["text_plain"] and "ّ" not in payload["text_plain"]
    assert "الله" in payload["text_plain"]


def test_should_reject_surah_when_out_of_range(client: TestClient) -> None:
    """A surah beyond 114 is not found rather than an empty verse."""
    assert client.get("/api/quran/200/1").status_code == 404


def test_should_reject_ayah_when_out_of_range(client: TestClient) -> None:
    """An ayah past the surah's length is not found."""
    assert client.get("/api/quran/1/99").status_code == 404


def test_should_find_verse_when_term_present(client: TestClient) -> None:
    """A distinctive phrase locates the verse that contains it."""
    payload = client.get("/api/quran/search", params={"q": "خلق عظيم"}).json()
    refs = {(v["surah"], v["ayah"]) for v in payload["items"]}
    assert (68, 4) in refs
    assert payload["total"] >= 1


def test_should_fold_letter_variants_when_searching(client: TestClient) -> None:
    """An alef-maqsura in the query folds to yaa, matching the diacritized verse."""
    payload = client.get("/api/quran/search", params={"q": "لعلى خلق"}).json()
    refs = {(v["surah"], v["ayah"]) for v in payload["items"]}
    assert (68, 4) in refs


def test_should_return_nothing_when_query_blank(client: TestClient) -> None:
    """A blank query matches nothing rather than every verse."""
    payload = client.get("/api/quran/search", params={"q": "   "}).json()
    assert payload["items"] == []
    assert payload["total"] == 0


def test_should_paginate_when_many_matches(client: TestClient) -> None:
    """limit caps the returned slice while total counts every match."""
    payload = client.get("/api/quran/search", params={"q": "الله", "limit": 5}).json()
    assert len(payload["items"]) == 5
    assert payload["total"] > 5  # "Allah" occurs in far more than five verses
