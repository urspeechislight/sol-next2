"""Tests for the canonical footnote-block splitter in backend.pipeline.text.

split_footnote_block is the serving-path shape (lossless, preamble preserved
as a null-marker entry); split_footnote_entries is its numbered projection
used by the pipeline's attach step. The corpus dry run measured ~17% of
fields carrying preamble text and ~11% carrying no numbered entries at all,
so both shapes are load-bearing, not edge cases.
"""

from __future__ import annotations

from backend.pipeline.text import (
    split_footnote_block,
    split_footnote_entries,
    split_footnote_entries_to_dict,
)


def test_should_split_numbered_block_into_marker_text_entries() -> None:
    block = "(1) الحاشية الأولى\n(2) الحاشية الثانية"

    assert split_footnote_block(block) == [
        ("1", "الحاشية الأولى"),
        ("2", "الحاشية الثانية"),
    ]


def test_should_preserve_preamble_as_null_marker_entry() -> None:
    block = "تتمة الحاشية من الصفحة السابقة\n(1) الحاشية الأولى"

    assert split_footnote_block(block) == [
        (None, "تتمة الحاشية من الصفحة السابقة"),
        ("1", "الحاشية الأولى"),
    ]


def test_should_yield_single_null_entry_for_freeform_block() -> None:
    block = "تعليق المحقق بلا ترقيم"

    assert split_footnote_block(block) == [(None, "تعليق المحقق بلا ترقيم")]


def test_should_yield_no_entries_for_blank_block() -> None:
    assert split_footnote_block("   \n  ") == []


def test_should_skip_numbered_entry_with_empty_text() -> None:
    block = "(1)\n(2) نص حقيقي"

    assert split_footnote_block(block) == [("2", "نص حقيقي")]


def test_should_keep_high_start_numbering_from_continuous_editions() -> None:
    block = "(17) حاشية بترقيم متصل\n(18) التالية"

    assert [marker for marker, _text in split_footnote_block(block)] == ["17", "18"]


def test_should_project_numbered_entries_only() -> None:
    block = "تتمة\n(1) الأولى"

    assert split_footnote_entries(block) == [("1", "الأولى")]
    assert split_footnote_entries_to_dict(block) == {"1": "الأولى"}


def test_should_fold_implausible_marker_jump_into_previous_entry() -> None:
    block = "(1) الأولى\n(2) الثانية\n(20856) نص مرجعي تسرب لبداية سطر"

    assert split_footnote_block(block) == [
        ("1", "الأولى"),
        ("2", "الثانية (20856) نص مرجعي تسرب لبداية سطر"),
    ]


def test_should_fold_non_increasing_marker_into_previous_entry() -> None:
    block = "(1) الأولى\n(2) الثانية\n(1) رقم متكرر"

    assert split_footnote_block(block) == [
        ("1", "الأولى"),
        ("2", "الثانية (1) رقم متكرر"),
    ]


def test_should_accept_high_first_marker_but_reject_a_later_implausible_jump() -> None:
    block = "(400) حاشية بترقيم متصل\n(401) التالية\n(99999) مرجع تسرب"

    assert split_footnote_block(block) == [
        ("400", "حاشية بترقيم متصل"),
        ("401", "التالية (99999) مرجع تسرب"),
    ]
