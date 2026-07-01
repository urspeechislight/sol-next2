"""Tests for the shared person-name decomposition utilities (names.py).

clean_name_text and the rijal/biography helpers (is_valid_person_name,
build_sentence_start_re) are exercised against the vendored config. The
kunya-start pattern is inlined here because its config section
(rijal_extraction) left with the unported rijal extractor; it returns to
config when that extractor lands. The hadith-critical name-cleanup path is
covered more deeply in test_name_extraction.py.
"""

from __future__ import annotations

from backend.patterns import cached_compile
from backend.pipeline.config import load_config
from backend.pipeline.names import (
    build_sentence_start_re,
    clean_name_text,
    is_valid_person_name,
)

_CFG = load_config()
_SENTENCE_START = build_sentence_start_re(
    tuple(_CFG.raw["narrator_extraction"]["sentence_start_disqualifiers"])
)
_GENEALOGY = next(regex for pid, regex in _CFG.compiled_patterns if pid == "GENEALOGY_CHAIN")
_KUNYA_START = cached_compile(r"^أ[بم][وي]\s+")


def test_should_replace_footnote_marker_with_space_when_cleaning_name() -> None:
    assert clean_name_text("محمد(2)بن") == "محمد بن"


def test_should_strip_trailing_punctuation_when_cleaning_name() -> None:
    assert clean_name_text("علي،") == "علي"


def test_should_collapse_repeated_spaces_when_cleaning_name() -> None:
    assert clean_name_text("محمد   بن") == "محمد بن"


def test_should_accept_name_containing_genealogy() -> None:
    assert is_valid_person_name("محمد بن إسماعيل", _SENTENCE_START, _GENEALOGY, _KUNYA_START)


def test_should_accept_name_starting_with_kunya() -> None:
    assert is_valid_person_name("أبو بكر", _SENTENCE_START, _GENEALOGY, _KUNYA_START)


def test_should_reject_editorial_prose_start() -> None:
    assert not is_valid_person_name("قد ذكر", _SENTENCE_START, _GENEALOGY, _KUNYA_START)


def test_should_reject_empty_name() -> None:
    assert not is_valid_person_name("", _SENTENCE_START, _GENEALOGY, _KUNYA_START)
