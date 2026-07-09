"""Tests for the name registry: what is (not) a narrator name, and how it is cleaned."""

from __future__ import annotations

import pytest

from backend.build.name_registry import clean_name, is_name, is_person_name, split_persons


@pytest.mark.parametrize(
    "raw",
    [
        "وسألت محمدا",
        "وبهذا الاسناد",
        "سألت أبي",
        "الأمالي للشيخ الطوسي",
        "للشريف المرتضى",
        "طبقته ورواياته",
        "شخصيته ووثاقته",
        "الشيخ الصدوق",
        "التاريخ الكبير",
    ],
)
def test_should_reject_non_name_strings(raw: str) -> None:
    """Isnad formulas, headings, book titles, and title-only refs are not person names."""
    assert is_person_name(raw) is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("سألت يحيى بن معين", "يحيى بن معين"),
        ("فعبد الله بن حفص الذي", "عبد الله بن حفص"),
        ("عبيد بن سلمان الكلبي ثم الطابخي", "عبيد بن سلمان الكلبي"),
        ("عمر بن كثير بن أفلح مولى أبي أيوب الأنصاري", "عمر بن كثير بن أفلح"),
        ("الشيخ محمد بن محمد بن النعمان", "محمد بن محمد بن النعمان"),
    ],
)
def test_should_clean_a_name_to_its_core(raw: str, expected: str) -> None:
    """A leading verb/title, a glued fa/wa, a trailing pronoun, and a stop token are removed."""
    assert clean_name(raw) == expected
    assert is_person_name(raw) is True


@pytest.mark.parametrize(
    "raw",
    [
        "أحمد بن محمد بن عيسى",
        "وهب بن منبه",
        "واصل بن عطاء",
        "فضل بن دكين",
        "أبو الشيخ الأصبهاني",
        "سالم بن عبد الله",
        "والنضر بن عبد الله",
    ],
)
def test_should_keep_real_names(raw: str) -> None:
    """Names whose first letter is wa/fa, or that carry a title tail, survive intact."""
    assert is_person_name(raw) is True


def test_should_peel_wa_when_name_head() -> None:
    """A leading wa/fa is peeled only when the remainder is a name head."""
    assert clean_name("والنضر بن عبد الله") == "النضر بن عبد الله"
    assert clean_name("وهب بن منبه") == "وهب بن منبه"


def test_should_split_waw_boundary() -> None:
    """A wāw glued to a kunya particle opens a new person; a wāw-initial name does not."""
    assert split_persons("أحمد بن محمد وأبي بكر") == ["أحمد بن محمد", "أبي بكر"]
    assert split_persons("عبد الله بن وهب") == ["عبد الله بن وهب"]


def test_should_screen_edge_names() -> None:
    """is_name is looser than is_person_name but still rejects a connective/verb lead."""
    assert is_name("محمد بن يحيى") is True
    assert is_name("سألت زرارة") is False
