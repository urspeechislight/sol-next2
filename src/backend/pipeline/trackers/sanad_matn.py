"""SanadMatn position tracker for the segment phase.

Tracks hadith numbering within the document. Each time a hadith-transmission
span is seen the counter increments, and the current hadith number is available
via current_path(). Ported from sol-next's src/trackers/sanad_matn.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.pipeline.models import HierarchyPath


@dataclass
class SanadMatnTracker:
    """FSM tracker for hadith position numbering.

    Advances on spans whose behavior matches the configured hadith behavior id.
    Produces a single-level HierarchyPath with the current hadith number.
    """

    _hadith_behavior_id: str = ""
    _hadith_counter: int = field(default=0)

    def should_advance(self, behavior: str) -> bool:
        """Return True when the behavior matches the hadith behavior id."""
        return bool(self._hadith_behavior_id) and behavior == self._hadith_behavior_id

    def advance(self, _span_text: str, _span_id: str) -> None:
        """Increment the hadith counter."""
        self._hadith_counter += 1

    def current_path(self) -> HierarchyPath:
        """Return the current hadith position as a HierarchyPath."""
        if self._hadith_counter == 0:
            return HierarchyPath(path=[], path_ids=[], depth=0)
        label = f"hadith_{self._hadith_counter}"
        return HierarchyPath(path=[label], path_ids=[label], depth=1)

    def reset(self) -> None:
        """Reset the hadith counter."""
        self._hadith_counter = 0
