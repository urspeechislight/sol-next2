"""Tests for ``repositories.corpus.passage_around``.

``passage_around`` is the fold-aware, budget-sized excerpt locator the build
layer uses to cut a tafsir commentary passage around a verse hit: roughly one
quarter of the budget as lead-in and three quarters as follow-on, each edge
snapped to a sentence boundary, with a bounded head excerpt when no window
matches.
"""

from __future__ import annotations

from backend.core.constants import CORPUS__SNIPPET_HEAD_CHARS
from backend.repositories.corpus import passage_around, search_windows

_VERSE = "الحمد لله رب العالمين الرحمن الرحيم مالك يوم الدين"


def _windows(verse: str = _VERSE) -> list[str]:
    return search_windows(verse, "exact")


def test_should_span_the_hit_with_lead_and_follow_on() -> None:
    """The excerpt brackets the verse: lead-in before, follow-on after, both
    cropped to roughly the requested budget."""
    lead = "مقدمة المفسر قبل الآية. " * 6
    tail = " ثم يشرح المفسر المعنى بعد الآية." * 8
    content = lead + _VERSE + tail
    found, passage = passage_around(content, _windows(), chars=200)
    assert found
    assert _VERSE in passage
    assert passage.startswith("…")
    assert passage.endswith("…")
    assert len(passage) <= len(_VERSE) + 200 + 2


def test_should_snap_the_left_edge_to_a_sentence_boundary() -> None:
    """A window opening mid-sentence trims the partial sentence at the edge,
    opening on the first boundary inside the window."""
    before = "x" * 300 + "مقدمة"
    between = "سياق قريب"
    content = before + "." + between + _VERSE + "y" * 300
    found, passage = passage_around(content, _windows(), chars=100)
    assert found
    assert "مقدمة" not in passage
    assert passage.startswith("…" + between)


def test_should_snap_the_right_edge_to_a_sentence_boundary() -> None:
    """A window closing mid-sentence trims the partial sentence at the edge,
    closing on the last boundary inside the window."""
    first = "شرح أول"
    after = "شرح ثان يمتد"
    content = "x" * 300 + _VERSE + first + "." + after + "y" * 300
    found, passage = passage_around(content, _windows(), chars=100)
    assert found
    assert after not in passage
    assert passage.endswith(first + ".…")


def test_should_match_through_diacritics_and_keep_original_orthography() -> None:
    """A voweled hit in the page locates against an unvoweled query, and the
    returned passage keeps the page's original voweled orthography."""
    voweled = "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
    content = "قال تعالى. " + voweled + " ثم يبدأ الشرح."
    windows = search_windows("الحمد لله رب العالمين", "exact")
    found, passage = passage_around(content, windows, chars=200)
    assert found
    assert voweled in passage


def test_should_not_underflow_when_the_hit_is_at_the_start() -> None:
    """A hit at offset zero opens the passage at the document start with no
    leading ellipsis and no negative index."""
    content = _VERSE + " ثم الشرح يطول" * 50
    found, passage = passage_around(content, _windows(), chars=100)
    assert found
    assert not passage.startswith("…")
    assert passage.startswith(_VERSE)


def test_should_not_overflow_when_the_hit_is_at_the_end() -> None:
    """A hit at the document end closes the passage at the document end with no
    trailing ellipsis and no index past the content length."""
    content = "مقدمة تسبق الآية. " * 30 + _VERSE
    found, passage = passage_around(content, _windows(), chars=100)
    assert found
    assert not passage.endswith("…")
    assert passage.endswith(_VERSE)


def test_should_clamp_the_head_to_the_snippet_budget_when_no_window_matches() -> None:
    """A miss returns ``(False, head)`` with the head sized to
    ``CORPUS__SNIPPET_HEAD_CHARS`` when the requested budget is smaller."""
    content = "لا آية هنا. " * 100
    found, head = passage_around(content, _windows(), chars=50)
    assert not found
    assert head.endswith("…")
    assert len(head) == CORPUS__SNIPPET_HEAD_CHARS + 1


def test_should_return_the_whole_document_on_a_miss_when_it_fits() -> None:
    """A miss on a document shorter than the head budget returns it intact,
    with no ellipsis."""
    content = "نص قصير بلا آية"
    found, head = passage_around(content, _windows(), chars=200)
    assert not found
    assert head == content
