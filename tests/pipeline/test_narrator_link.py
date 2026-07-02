"""Tests for the build-time narrator-to-registry linker (narrator_link.py).

The matching semantics mirror the frontend's retired narrators.ts matcher:
registry-name tokens match the extracted name's tokens in order from the
start, connectives in the text that the registry name omits are skipped,
longest registry name wins, rijal beats canonical for the same name, and
single-token names never link.
"""

from __future__ import annotations

from backend.build.narrator_link import NarratorLinker

_LINKER = NarratorLinker.from_names(
    [
        ("canonical", "مالك بن أنس", 7),
        ("rijal", "مالك بن أنس", 3),
        ("rijal", "مالك بن أنس الأصبحي", 4),
        ("rijal", "عائشة", 5),
    ]
)


def test_should_link_exact_name() -> None:
    link = _LINKER.link("مالك بن أنس")
    assert link is not None
    assert (link.origin, link.registry_id) == ("rijal", 3)


def test_should_prefer_longest_registry_name() -> None:
    link = _LINKER.link("مالك بن أنس الأصبحي عن نافع")
    assert link is not None
    assert link.registry_id == 4


def test_should_prefer_rijal_over_canonical_for_same_name() -> None:
    link = _LINKER.link("مالك بن أنس قال")
    assert link is not None
    assert link.origin == "rijal"


def test_should_skip_connective_tokens_in_text() -> None:
    linker = NarratorLinker.from_names([("rijal", "مالك أنس", 9)])
    link = linker.link("مالك بن أنس")
    assert link is not None
    assert link.registry_id == 9


def test_should_not_link_single_token_registry_names() -> None:
    assert _LINKER.link("عائشة") is None


def test_should_not_link_unknown_names() -> None:
    assert _LINKER.link("لا تدخل على المضمر فلا يقال") is None
    assert _LINKER.link("") is None
