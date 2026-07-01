"""KitabBabFasl hierarchy tracker for the segment phase.

Tracks the three-level heading structure (kitab/bab/fasl) common in classical
Arabic manuscripts. Reads heading-prefix configuration from the HEADING_MARKER
pattern in config/sol.yaml. Ported from sol-next's src/trackers/kitab_bab_fasl.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.core.constants import HADITH__PATTERN_HEADING_MARKER
from backend.patterns import CompiledPattern
from backend.pipeline.models import HierarchyPath


@dataclass
class KitabBabFaslTracker:
    """FSM tracker for hierarchical heading levels.

    Levels and their Arabic prefixes come from config's HEADING_MARKER
    hierarchy_levels. When a SECTION_HEADING span is seen, the tracker picks the
    level from the text prefix and clears all deeper levels.
    """

    _level_names: tuple[str, ...] = ()
    _prefix_to_level: dict[str, str] = field(default_factory=dict)
    _all_prefixes: tuple[str, ...] = ()
    _top_level_prefixes: frozenset[str] = field(default_factory=frozenset)
    _heading_stop_patterns: tuple[str, ...] = ()
    _attribution_re: CompiledPattern | None = field(default=None, repr=False)
    _heading_behavior_id: str = "SECTION_HEADING"
    _heading_counter: int = field(default=0)
    _state: dict[str, tuple[str, str]] = field(default_factory=dict)

    def should_advance(self, behavior: str) -> bool:
        """Return True when the behavior is a section heading."""
        return behavior == self._heading_behavior_id

    def advance(self, span_text: str, _span_id: str) -> None:
        """Update hierarchy state when a SECTION_HEADING span is encountered.

        Determines the heading level from the text prefix, stores the heading
        title (not the full span text), and clears deeper levels when a higher
        level changes.
        """
        heading_line = _extract_heading_line(
            span_text,
            self._all_prefixes,
            self._top_level_prefixes,
            self._attribution_re,
            self._heading_stop_patterns,
        )
        self._heading_counter += 1
        heading_id = f"heading_{self._heading_counter:03d}"
        level = self._resolve_level(heading_line)
        self._state[level] = (heading_line, heading_id)
        if level in self._level_names:
            level_idx = self._level_names.index(level)
            for deeper in self._level_names[level_idx + 1 :]:
                self._state.pop(deeper, None)

    def current_path(self) -> HierarchyPath:
        """Return the current hierarchy state as a HierarchyPath."""
        path: list[str] = []
        path_ids: list[str] = []
        for level_name in self._level_names:
            if level_name in self._state:
                text, hid = self._state[level_name]
                path.append(text)
                path_ids.append(hid)
        return HierarchyPath(path=path, path_ids=path_ids, depth=len(path))

    def reset(self) -> None:
        """Reset tracker to initial state."""
        self._heading_counter = 0
        self._state.clear()

    def _resolve_level(self, heading_line: str) -> str:
        """Match a heading line to its hierarchy level via earliest prefix."""
        best_level = self._level_names[0] if self._level_names else "kitab"
        best_pos = len(heading_line)
        for prefix in self._all_prefixes:
            pos = heading_line.find(prefix)
            if pos != -1 and pos < best_pos:
                best_pos = pos
                best_level = self._prefix_to_level[prefix]
        return best_level


def _extract_heading_line(
    span_text: str,
    all_prefixes: tuple[str, ...] = (),
    top_level_prefixes: frozenset[str] = frozenset(),
    attribution_re: CompiledPattern | None = None,
    heading_stop_patterns: tuple[str, ...] = (),
) -> str:
    """Extract the heading title from a SECTION_HEADING span's text.

    Classical Arabic chapter headings can be long and wrap across lines. Finds
    the first line with a known heading prefix; top-level (kitab) titles are
    single-line, lower levels collect continuation lines until a content
    boundary (blank line, new prefix, attribution verb, or stop pattern). Falls
    back to the first non-empty line if no prefix matches.
    """
    lines = span_text.split("\n")
    heading_start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and any(p in stripped for p in all_prefixes):
            heading_start = i
            break
    if heading_start == -1:
        for line in lines:
            stripped = line.strip()
            if stripped:
                return stripped
        return span_text.strip()

    first_heading_line = lines[heading_start].strip()
    if any(p in first_heading_line for p in top_level_prefixes):
        return first_heading_line

    collected = [first_heading_line]
    for line in lines[heading_start + 1 :]:
        stripped = line.strip()
        if not stripped:
            break
        if any(p in stripped for p in all_prefixes):
            break
        if attribution_re is not None and attribution_re.search(stripped):
            break
        if heading_stop_patterns and any(sp in stripped for sp in heading_stop_patterns):
            break
        collected.append(stripped)
    return " ".join(collected)


def parse_hierarchy_levels(
    raw_patterns: list[dict[str, Any]],
) -> tuple[tuple[str, ...], dict[str, str], tuple[str, ...], frozenset[str], tuple[str, ...]]:
    """Extract hierarchy level mappings from the HEADING_MARKER pattern config.

    Reads hierarchy_levels and heading_stop_patterns from the HEADING_MARKER
    pattern. Prefixes are sorted longest-first so longer prefixes match before
    shorter ones. Returns (level_names, prefix_to_level, all_prefixes,
    top_level_prefixes, heading_stop_patterns).
    """
    heading_entry = None
    for entry in raw_patterns:
        if entry["id"] == HADITH__PATTERN_HEADING_MARKER:
            heading_entry = entry
            break
    if heading_entry is None or "hierarchy_levels" not in heading_entry:
        return (), {}, (), frozenset(), ()

    hierarchy = heading_entry["hierarchy_levels"]
    level_names = tuple(hierarchy.keys())
    prefix_to_level: dict[str, str] = {}
    for level, prefixes in hierarchy.items():
        for prefix in prefixes:
            prefix_to_level[prefix] = level
    all_prefixes = tuple(sorted(prefix_to_level.keys(), key=len, reverse=True))
    top_level = level_names[0] if level_names else None
    top_level_prefixes = frozenset(hierarchy.get(top_level, []) if top_level else [])
    heading_stop_patterns = tuple(heading_entry.get("heading_stop_patterns", []))
    return level_names, prefix_to_level, all_prefixes, top_level_prefixes, heading_stop_patterns
