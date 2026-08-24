"""Boolean + bilingual behavior of the local search paths (Quran verses).

Exercises search_verses against the real served Quran data: Arabic AND/NOT,
English matching, and diacritic-insensitive matching through boolean clauses.
"""

from __future__ import annotations

from backend.repositories.quran import search_verses


def test_should_require_all_include_clauses() -> None:
    """AND narrows relative to each clause alone."""
    _, total_allah = search_verses("الله", limit=1, offset=0)
    _, total_both = search_verses("الله + رحيم", limit=1, offset=0)
    assert total_both <= total_allah
    assert total_both > 0


def test_should_exclude_negated_clauses() -> None:
    """Count arithmetic: pages(A) = pages(A AND B) + pages(A NOT B)."""
    _, base = search_verses("الله", limit=1, offset=0)
    _, both = search_verses("الله + رحيم", limit=1, offset=0)
    _, without = search_verses("الله NOT رحيم", limit=1, offset=0)
    assert base == both + without


def test_should_match_english_verse_text() -> None:
    """English queries match the translation column, plain and boolean."""
    _, en_total = search_verses("merciful", limit=1, offset=0)
    assert en_total > 0
    _, mixed = search_verses("merciful + الله", limit=1, offset=0)
    assert mixed > 0
    _, excluded = search_verses("merciful NOT الله", limit=1, offset=0)
    assert excluded < en_total


def test_should_fold_diacritics_through_boolean_clauses() -> None:
    """A fully voweled clause matches as if unvoweled (fold applies per clause)."""
    _, plain = search_verses("بسم", limit=1, offset=0)
    _, voweled = search_verses("بِسْمِ + الله", limit=1, offset=0)
    assert voweled > 0
    assert voweled <= plain
