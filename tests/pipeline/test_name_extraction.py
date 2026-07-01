"""Tests for the canonical person-name cleanup pipeline (name_extraction.py).

extract_person_name is the hadith extractor's entry point into name cleanup, so
the boundary-crop, end-position-crop, compound-prefix extension, dangling-
connector strip, leading-clitic strip, and empty->None paths are all covered,
plus the two exposed helpers strip_dangling_tail and strip_leading_clitic.
"""

from __future__ import annotations

from collections.abc import Iterable

from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.name_extraction import (
    NameOptions,
    extract_person_name,
    strip_dangling_tail,
    strip_leading_clitic,
)

_NEVER_CROP = cached_compile(r"[,;]")
_COMMA_CROP = cached_compile(r"[،]")


def _opts(
    boundary_regex: CompiledPattern = _NEVER_CROP,
    *,
    end_positions: Iterable[int] = (),
) -> NameOptions:
    """A NameOptions with the config clitic threshold, overridable per test."""
    return NameOptions(
        boundary_regex=boundary_regex,
        clitic_min_word_chars=5,
        end_positions=end_positions,
    )


def _extract(text: str, start: int, end: int, opts: NameOptions) -> tuple[str, int, int]:
    """extract_person_name with the None branch asserted away for unpacking."""
    result = extract_person_name(text, start, end, opts)
    assert result is not None
    return result


def test_should_drop_trailing_patronymic_connectors() -> None:
    assert strip_dangling_tail("محمد بن") == "محمد"
    assert strip_dangling_tail("محمد بن ابن") == "محمد"
    assert strip_dangling_tail("محمد") == "محمد"


def test_should_strip_leading_clitic_on_long_word() -> None:
    assert strip_leading_clitic("ومحمد", 5) == ("محمد", 1)


def test_should_strip_leading_clitic_before_hamza_alef() -> None:
    assert strip_leading_clitic("وأحمد", 5) == ("أحمد", 1)


def test_should_leave_short_candidate_untouched() -> None:
    assert strip_leading_clitic("وب", 5) == ("وب", 0)


def test_should_crop_at_boundary_regex_hit() -> None:
    text = "محمد، ثم قال"
    cleaned, start, end = _extract(text, 0, len(text), _opts(_COMMA_CROP))
    assert cleaned == "محمد"
    assert text[start:end] == "محمد"


def test_should_crop_at_end_position_anchor() -> None:
    text = "john smith jr"
    cut = text.index(" jr")
    cleaned, start, end = _extract(text, 0, len(text), _opts(end_positions=(cut,)))
    assert cleaned == "john smith"
    assert text[start:end] == "john smith"


def test_should_extend_back_to_compound_prefix() -> None:
    text = "حدثنا عبد الله بن محمد"
    start = text.index("الله")
    cleaned, abs_start, abs_end = _extract(text, start, len(text), _opts())
    assert cleaned == "عبد الله بن محمد"
    assert abs_start == text.index("عبد")
    assert text[abs_start:abs_end] == "عبد الله بن محمد"


def test_should_strip_leading_clitic_in_full_pipeline() -> None:
    text = "ومحمد بن علي"
    cleaned, start, end = _extract(text, 0, len(text), _opts())
    assert cleaned == "محمد بن علي"
    assert text[start:end] == "محمد بن علي"


def test_should_return_none_when_cleaned_text_is_empty() -> None:
    text = "،"
    assert extract_person_name(text, 0, len(text), _opts(_COMMA_CROP)) is None
