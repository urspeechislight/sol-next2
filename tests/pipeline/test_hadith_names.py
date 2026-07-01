"""Tests for the co-narrator splitting helpers (hadith_names.py).

split_co_narrators and snap_name_end_to_word_boundary are the hadith extractor's
name-slice helpers; the comma-waw / bare-waw splits and their guards, plus the
mid-word snap, are all covered.
"""

from __future__ import annotations

from backend.pipeline.hadith_names import (
    snap_name_end_to_word_boundary,
    split_co_narrators,
)

_RELATIVE_REFS = ["أبيه", "أبوه", "أمه"]


def test_should_split_on_comma_waw_unconditionally() -> None:
    assert split_co_narrators("زيد ، وعمر", _RELATIVE_REFS) == ["زيد", "عمر"]


def test_should_split_on_bare_waw() -> None:
    assert split_co_narrators("زيد وعمر", _RELATIVE_REFS) == ["زيد", "عمر"]


def test_should_not_split_waw_after_ibn() -> None:
    assert split_co_narrators("بن وهب", _RELATIVE_REFS) == ["بن وهب"]


def test_should_not_split_waw_before_relative_reference() -> None:
    assert split_co_narrators("زيد وأبيه", _RELATIVE_REFS) == ["زيد وأبيه"]


def test_should_not_split_waw_before_identity_clarification() -> None:
    assert split_co_narrators("زيد وهو", _RELATIVE_REFS) == ["زيد وهو"]


def test_should_return_single_part_when_no_conjunction() -> None:
    assert split_co_narrators("زيد", _RELATIVE_REFS) == ["زيد"]


def test_should_extend_to_word_boundary_when_landed_mid_word() -> None:
    text = "عقيل بن"
    assert snap_name_end_to_word_boundary(text, 1) == len("عقيل")


def test_should_return_pos_unchanged_when_already_at_boundary() -> None:
    text = "عقيل بن"
    boundary_pos = len("عقيل ")  # lands on the space, preceded by a letter end
    assert snap_name_end_to_word_boundary(text, boundary_pos) == boundary_pos


def test_should_return_pos_unchanged_when_past_end() -> None:
    assert snap_name_end_to_word_boundary("عقيل", 100) == 100


def test_should_return_zero_when_pos_is_zero() -> None:
    assert snap_name_end_to_word_boundary("عقيل", 0) == 0
