"""TOC-based content boundary detection for the segment phase.

Finds where main content starts by testing TOC entry titles against the
content-start patterns compiled from config. Pages before the content start are
editorial front-matter. Ported from sol-next's src/utils/toc.py.
"""

from __future__ import annotations

from typing import Any

from backend.patterns import CompiledPattern, cached_compile, strip_tashkeel

_BRACKET_STRIP: CompiledPattern = cached_compile(r"[\[\](){}«»]")


def find_content_start_page(
    toc: list[dict[str, Any]],
    content_start_patterns: list[CompiledPattern],
) -> int | None:
    """Find the page where main content begins, based on TOC titles.

    Walks TOC entries in page order and returns the page_number of the first
    whose cleaned title matches any content-start pattern, or None if none match.
    Brackets and tashkeel are stripped first so vowelled titles match unvowelled
    config patterns.
    """
    if not toc or not content_start_patterns:
        return None
    sorted_entries = sorted(toc, key=lambda e: e.get("page_number", 0))
    for entry in sorted_entries:
        title = entry.get("title", "")
        cleaned = _BRACKET_STRIP.sub("", title).strip()
        cleaned = strip_tashkeel(cleaned)
        if not cleaned:
            continue
        for pattern in content_start_patterns:
            if pattern.search(cleaned):
                return entry["page_number"]
    return None
