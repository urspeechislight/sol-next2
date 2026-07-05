"""Numbered-entry position tracker for the segment phase.

Each printed entry within a chapter is a distinct leaf in the hierarchy. The
leaf changes exactly when a span opens a new printed entry number (``N -``),
and every span without one continues the current entry. That models the edition
faithfully: a numbered hadith and its unnumbered matn continuation share one
leaf, while two different printed numbers never share a leaf (the earlier
hadith-only counter left numbered entries and verse/commentary spans inheriting
a neighbour's node, conflating distinct entries). The visible label is the
printed number; the node id is a monotonic counter so graph identity stays
unique. Ported and generalized from sol-next's src/trackers/sanad_matn.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.models import HierarchyPath
from backend.pipeline.trackers import TrackerProtocol

_LEADING_ENTRY_NUMBER: CompiledPattern = cached_compile(r"^\s*\*?\s*\(?([0-9٠-٩]+)(?:\s*[.\-]|\))")
_NODE_ID_FORMAT: str = "entry_{index:04d}"


def _leading_entry_number(span_text: str) -> str | None:
    """The printed ordinal when the span opens with a numbered marker, else None.

    Mirrors the NUMBERED_ENTRY pattern's accepted forms (``5 -`` / ``5.`` /
    ``5)`` / ``(5)`` / ``* 5 -``) so a book numbered with parentheses or dots
    advances one entry per printed number rather than sharing a node."""
    match = _LEADING_ENTRY_NUMBER.match(span_text)
    if match is None:
        return None
    return match.group(1)


@dataclass
class SanadMatnTracker(TrackerProtocol):
    """FSM tracker keyed on printed entry numbers.

    Opens a new leaf on any span that starts with a printed entry number; all
    other spans continue the current entry. Number-driven rather than
    behavior-driven, so a split hadith's unnumbered matn half stays under its
    isnad's entry and a numbered verse or commentary gets its own leaf.
    """

    _counter: int = field(default=0)
    _current: tuple[str, str] | None = field(default=None)

    def should_advance(self, _behavior: str, _anchor: object | None, /) -> bool:
        """Every span is inspected; advance() decides from the text (args unused)."""
        return True

    def advance(self, span_text: str, _span_id: str, _anchor: object | None, /) -> None:
        """Open a new leaf when the span starts a printed entry; else keep the current."""
        number = _leading_entry_number(span_text)
        if number is None:
            return
        self._counter += 1
        self._current = (f"entry_{number}", _NODE_ID_FORMAT.format(index=self._counter))

    def current_path(self) -> HierarchyPath:
        """Return the current entry position as a HierarchyPath."""
        if self._current is None:
            return HierarchyPath(path=[], path_ids=[], depth=0)
        label, node_id = self._current
        return HierarchyPath(path=[label], path_ids=[node_id], depth=1)

    def reset(self) -> None:
        """Reset the entry counter."""
        self._counter = 0
        self._current = None
