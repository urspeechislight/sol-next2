"""TOC-driven hierarchy tracker for the segment phase.

When a book ships a table of contents, its editorial section titles are the
authoritative document structure. That is far more reliable than reconstructing
the structure from pattern-detected headings, which misclassify a numbered
hadith, a cited book title, or a stray matn fragment as a chapter and so
fabricate nodes the book never had. This tracker advances only on spans that
carry a confirmed TOC anchor (see ``toc_alignment``), nesting each title at the
anchor's inferred level and clearing deeper levels, so the emitted hierarchy is
exactly the book's own contents.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.pipeline.models import HierarchyPath
from backend.pipeline.toc_alignment import TocAnchor
from backend.pipeline.trackers import TrackerProtocol

TOC__NODE_ID_FORMAT: str = "toc_{index:03d}"


@dataclass
class TocHierarchyTracker(TrackerProtocol):
    """Hierarchy tracker keyed on confirmed TOC anchors.

    State maps an anchor level to the (title, node_id) open at that level. A new
    anchor at level L replaces level L and clears every deeper level, so the path
    is the chain of enclosing TOC sections. Spans between anchors keep the last
    anchor's path, which groups them under the section that opened them.
    """

    _counter: int = field(default=0)
    _state: dict[int, tuple[str, str]] = field(default_factory=dict[int, tuple[str, str]])

    def should_advance(self, _behavior: str, anchor: TocAnchor | None, /) -> bool:
        """Advance only when the span carries a TOC anchor."""
        return anchor is not None

    def advance(self, _span_text: str, _span_id: str, anchor: TocAnchor | None, /) -> None:
        """Open the anchor's title at its level and clear deeper levels."""
        if anchor is None:
            return
        self._counter += 1
        node_id = TOC__NODE_ID_FORMAT.format(index=self._counter)
        self._state[anchor.level] = (anchor.title, node_id)
        for deeper in [level for level in self._state if level > anchor.level]:
            del self._state[deeper]

    def current_path(self) -> HierarchyPath:
        """Return the enclosing TOC sections, shallowest level first."""
        path: list[str] = []
        path_ids: list[str] = []
        for level in sorted(self._state):
            title, node_id = self._state[level]
            path.append(title)
            path_ids.append(node_id)
        return HierarchyPath(path=path, path_ids=path_ids, depth=len(path))

    def reset(self) -> None:
        """Reset tracker to initial state."""
        self._counter = 0
        self._state.clear()
