"""Tests for the name registry: what is (not) a narrator name, and how it is cleaned."""

from __future__ import annotations

import pytest

from backend.build.name_registry import clean_name, is_person_name


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
        ("عبيد بن سلمان الكلبي ثم الطابخي", "عبيد بن سلمان الكلبي ثم الطابخي"),
        ("عمر بن كثير بن أفلح مولى أبي أيوب الأنصاري", "عمر بن كثير بن أفلح"),
        ("الشيخ محمد بن محمد بن النعمان", "محمد بن محمد بن النعمان"),
        ("أحمد بن محمد بن عيسى الأشعري 191", "أحمد بن محمد بن عيسى الأشعري"),
        ("أحمد بن محمد بن عيسى مرفوعا عنه", "أحمد بن محمد بن عيسى"),
        ("عيسى بن الجراح المصري اتهمه أبو الحسين", "عيسى بن الجراح المصري"),
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


@pytest.mark.parametrize(
    "title",
    [
        "الموطأ لمالك",
        "المستدرك على الصحيحين",
        "الإصابة في تمييز الصحابة",
        "الميزان للذهبي",
        "الضعفاء الكبير",
    ],
)
def test_should_reject_common_book_titles(title: str) -> None:
    """A work whose title leads with a book word is screened out, not served as a person.

    ``al-X al-Y`` book titles (``الضعفاء الكبير``) share the exact shape of real
    names (``الحسن البصري``), so no structural signal separates them. ``_BOOK_LEADS``
    is the bounded reference lexicon of book-title lead words that resolves the
    collision, the same kind of closed lookup as ``_TITLE_LEADS``.
    """
    assert is_person_name(title) is False
