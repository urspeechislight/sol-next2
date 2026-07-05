"""Hierarchy trackers for the segment phase.

Trackers are FSMs that run during the segmentation pass. Each observes span
behaviors and maintains state that produces HierarchyPath values for document
structure tracking. TrackerProtocol defines the interface; TrackerOrchestrator
runs all registered trackers and merges their output into one HierarchyPath.
Ported from sol-next's src/trackers/__init__.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from backend.pipeline.models import HierarchyPath

if TYPE_CHECKING:
    from backend.pipeline.toc_alignment import TocAnchor


@runtime_checkable
class TrackerProtocol(Protocol):
    """Interface for document structure trackers.

    ``anchor`` is the span's confirmed TOC anchor, or None. A TOC-driven tracker
    keys on it; pattern-driven trackers ignore it and key on ``behavior``.
    """

    def should_advance(self, behavior: str, anchor: TocAnchor | None) -> bool:
        """Return True if this tracker should advance on the given span."""
        ...

    def advance(self, span_text: str, span_id: str, anchor: TocAnchor | None) -> None:
        """Update tracker state for a span this tracker advances on."""
        ...

    def current_path(self) -> HierarchyPath:
        """Return the current hierarchy path from this tracker's state."""
        ...

    def reset(self) -> None:
        """Reset tracker to initial state."""
        ...


class TrackerOrchestrator:
    """Runs all registered trackers and merges their hierarchy paths.

    During the segmentation pass, advance() delegates to each tracker whose
    should_advance() returns True for the current behavior. current_path()
    merges all tracker paths by concatenation, primary tracker first.
    """

    def __init__(self, trackers: list[TrackerProtocol]) -> None:
        self._trackers = trackers

    def advance(
        self, behavior: str, span_text: str, span_id: str, anchor: TocAnchor | None
    ) -> None:
        """Delegate advance to each tracker that handles this span."""
        for tracker in self._trackers:
            if tracker.should_advance(behavior, anchor):
                tracker.advance(span_text, span_id, anchor)

    def current_path(self) -> HierarchyPath:
        """Merge paths from all trackers into a single HierarchyPath."""
        merged_path: list[str] = []
        merged_ids: list[str] = []
        for tracker in self._trackers:
            hp = tracker.current_path()
            merged_path.extend(hp.path)
            merged_ids.extend(hp.path_ids)
        return HierarchyPath(
            path=merged_path,
            path_ids=merged_ids,
            depth=len(merged_path),
        )
