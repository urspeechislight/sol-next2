"""Tests for the canonical person-name cleanup pipeline (name_extraction.py).

extract_person_name is the hadith extractor's entry point into name cleanup:
the boundary-crop (with footnote-marker paren skip), the clean_name_text
footnote/punctuation cleanup, and the empty-to-None path are covered.
"""

from __future__ import annotations

from backend.patterns import cached_compile
from backend.pipeline.name_extraction import clean_name_text, extract_person_name

_NEVER_CROP = cached_compile(r"[,;]")
_COMMA_CROP = cached_compile(r"[،]")
_PAREN_CROP = cached_compile(r"[(،]")


def test_should_replace_footnote_marker_with_space_when_cleaning_name() -> None:
    assert clean_name_text("محمد(2)بن") == "محمد بن"


def test_should_strip_trailing_punctuation_when_cleaning_name() -> None:
    assert clean_name_text("علي،") == "علي"


def test_should_collapse_repeated_spaces_when_cleaning_name() -> None:
    assert clean_name_text("محمد   بن") == "محمد بن"


def test_should_crop_at_boundary_regex_hit() -> None:
    text = "محمد، ثم قال"
    result = extract_person_name(text, 0, len(text), _COMMA_CROP)
    assert result is not None
    cleaned, start, end = result
    assert cleaned == "محمد"
    assert text[start:end] == "محمد"


def test_should_skip_footnote_paren_when_cropping() -> None:
    text = "محمد (2) بن علي، ثم"
    result = extract_person_name(text, 0, len(text), _PAREN_CROP)
    assert result is not None
    cleaned, _, _ = result
    assert cleaned == "محمد بن علي"


def test_should_pass_through_when_no_boundary_hit() -> None:
    text = "محمد بن علي"
    result = extract_person_name(text, 0, len(text), _NEVER_CROP)
    assert result is not None
    cleaned, start, end = result
    assert cleaned == "محمد بن علي"
    assert text[start:end] == "محمد بن علي"


def test_should_return_none_when_cleaned_text_is_empty() -> None:
    text = "،"
    assert extract_person_name(text, 0, len(text), _COMMA_CROP) is None
