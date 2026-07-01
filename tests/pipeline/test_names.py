"""Tests for the shared person-name decomposition utilities (names.py).

clean_name_text and the rijal/biography helpers (is_valid_person_name,
extract_kunya, extract_laqab, build_sentence_start_re) are exercised against the
vendored config. The hadith-critical name-cleanup path is covered more deeply in
test_name_extraction.py.
"""

from __future__ import annotations

from backend.patterns import cached_compile
from backend.pipeline.config import load_config
from backend.pipeline.models import Pattern
from backend.pipeline.names import (
    build_sentence_start_re,
    clean_name_text,
    extract_kunya,
    extract_laqab,
    is_valid_person_name,
)

_CFG = load_config()
_SENTENCE_START = build_sentence_start_re(
    tuple(_CFG.raw["narrator_extraction"]["sentence_start_disqualifiers"])
)
_GENEALOGY = next(regex for pid, regex in _CFG.compiled_patterns if pid == "GENEALOGY_CHAIN")
_KUNYA_START = cached_compile(_CFG.raw["rijal_extraction"]["kunya_start"])


def test_should_replace_footnote_marker_with_space_when_cleaning_name() -> None:
    assert clean_name_text("محمد(2)بن") == "محمد بن"


def test_should_strip_trailing_punctuation_when_cleaning_name() -> None:
    assert clean_name_text("علي،") == "علي"


def test_should_collapse_repeated_spaces_when_cleaning_name() -> None:
    assert clean_name_text("محمد   بن") == "محمد بن"


def test_should_return_none_when_no_kunya_present() -> None:
    assert extract_kunya("محمد بن إسماعيل", _CFG) is None


def test_should_extract_kunya_when_present() -> None:
    result = extract_kunya("حدثنا أبو القاسم", _CFG)
    assert result is not None
    kunya, start, _ = result
    assert kunya == "أبو القاسم"
    assert start == len("حدثنا ")


def test_should_return_none_when_no_laqab_marker() -> None:
    assert extract_laqab("نص بلا لقب", [], _CFG) is None


def test_should_extract_laqab_up_to_boundary_when_marker_present() -> None:
    span_text = "الملطي الخضري، ثم"
    marker = Pattern(
        pattern_id="LAQAB_MARKER",
        matched_text="الملطي",
        char_start=0,
        char_end=len("الملطي"),
    )
    result = extract_laqab(span_text, [marker], _CFG)
    assert result is not None
    laqab, start, end = result
    assert laqab == "الخضري"
    assert span_text[start:end] == "الخضري"


def test_should_accept_name_containing_genealogy() -> None:
    assert is_valid_person_name("محمد بن إسماعيل", _SENTENCE_START, _GENEALOGY, _KUNYA_START)


def test_should_accept_name_starting_with_kunya() -> None:
    assert is_valid_person_name("أبو بكر", _SENTENCE_START, _GENEALOGY, _KUNYA_START)


def test_should_reject_editorial_prose_start() -> None:
    assert not is_valid_person_name("قد ذكر", _SENTENCE_START, _GENEALOGY, _KUNYA_START)


def test_should_reject_empty_name() -> None:
    assert not is_valid_person_name("", _SENTENCE_START, _GENEALOGY, _KUNYA_START)
