"""Phase 2: SEGMENT — span boundaries, behavior routing, hierarchy tracking.

Input:  Manuscript with pages populated (Phase 1 / reader page rows).
Output: Manuscript with spans populated, each carrying .behavior and .hierarchy.

Two jobs run in one sequential pass over the pages joined into one combined
string (so a hadith flowing across pages stays one span — page breaks are not
boundaries):

1. Boundary detection + behavior routing — split the combined text, merge the
   isnad-continuation false splits, then route each paragraph to a behavior via
   the config table.
2. Hierarchy tracking — a TrackerOrchestrator advances FSM trackers on each
   span; each span's .hierarchy is the merged FSM state at that point.

Ported from sol-next's src/phases/segment.py, decomposed under the file-size
and function-size caps: the routing table lives in _segment_routing and the
pattern-detection / heading split in _segment_detect. The quran-corpus pattern
augmentation is omitted (the quran service is not wired in this milestone); the
routing table reaches GENERAL_PROSE directly. Every compiled pattern comes from
the central backend.patterns module; this module imports no regex machinery.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from backend.core.constants import (
    HADITH__BEHAVIOR_EDITORIAL_FRONTMATTER,
    HADITH__BEHAVIOR_TRANSMISSION,
    HADITH__PATTERN_HEADING_MARKER,
    HADITH__SPAN_TYPE_PARAGRAPH,
)
from backend.core.logging import get_logger
from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline._segment_detect import detect_patterns, split_heading_from_content
from backend.pipeline._segment_routing import (
    BehaviorRule,
    parse_behavior_rules,
    parse_start_thresholds,
    route_behavior,
    validate_required_behaviors,
)
from backend.pipeline.boundaries import build_merge_cues, merge_isnad_continuations
from backend.pipeline.boundaries_headings import (
    HeadingCues,
    build_inline_heading_re,
    split_at_inline_headings,
)
from backend.pipeline.config import Config
from backend.pipeline.contracts import validate_manuscript_for_phase
from backend.pipeline.failure_budget import enforce_failure_budget
from backend.pipeline.headings import (
    drop_heading_for_narrative,
    filter_heading_disqualifiers,
    filter_heading_shape,
    parse_heading_disqualifiers,
    parse_heading_qualifiers,
)
from backend.pipeline.models import Manuscript, ManuscriptPage, Pattern, Span
from backend.pipeline.splitting import (
    SplitLayout,
    build_combined_text,
    compile_boundary_splitter,
    split_with_page_tracking,
)
from backend.pipeline.text import attach_footnote_text, split_footnote_entries_to_dict
from backend.pipeline.toc import find_content_start_page
from backend.pipeline.toc_alignment import TocAnchor, find_toc_anchors
from backend.pipeline.trackers import TrackerOrchestrator, TrackerProtocol
from backend.pipeline.trackers.kitab_bab_fasl import KitabBabFaslTracker, parse_hierarchy_levels
from backend.pipeline.trackers.sanad_matn import SanadMatnTracker

_logger = get_logger("shia-library.segment")

HADITH__SPAN_ID_FORMAT: Final[str] = "{manifestation_id}_s{index:04d}"
_NAME_CONTINUATION_REGEX: CompiledPattern = cached_compile(r"\s*ال[؀-ۿ]")


@dataclass
class _SegmentContext:
    """All segment-phase inputs parsed from config + manuscript, built once."""

    config: Config
    compiled_patterns: dict[str, CompiledPattern]
    behavior_rules: list[BehaviorRule]
    start_thresholds: dict[str, int]
    orchestrator: TrackerOrchestrator
    boundary_regex: CompiledPattern
    heading_disqualifiers: list[CompiledPattern]
    heading_qualifiers: list[CompiledPattern]
    narrative_genres: frozenset[str]
    attribution_regex: CompiledPattern | None
    attribution_strong_regex: CompiledPattern | None
    inline_heading_regex: CompiledPattern | None
    heading_marker_regex: CompiledPattern | None
    toc: list[dict[str, Any]]
    content_start_page: int | None
    name_prefix_tokens: frozenset[str]


@dataclass
class _ParagraphLayout:
    """The split, merged, heading-split paragraphs segment emits spans from."""

    paragraphs: list[tuple[str, int, int]]
    anchor_by_key: dict[tuple[str, int, int], TocAnchor]
    page_footnotes: dict[int, dict[str, str]]


def segment(manuscript: Manuscript, config: Config) -> Manuscript:
    """Detect span boundaries, assign behaviors, and track hierarchy.

    Joins all content-page texts into one combined string so the boundary
    splitter operates across page boundaries. Populates ``manuscript.spans``;
    every span exits with a non-None ``behavior`` and ``hierarchy``.

    Raises SegmentError when pattern compilation or the routing failure budget
    is breached; ContractError when the manuscript lacks pages.
    """
    validate_manuscript_for_phase(manuscript, "segment")
    validate_required_behaviors(config.behaviors)
    ctx = _build_segment_context(manuscript, config)
    content_pages = [page for page in manuscript.pages if page.is_content]
    if not content_pages:
        return manuscript
    layout = _build_paragraphs(content_pages, ctx)
    unclassified_count, content_span_count = _emit_spans(manuscript, layout, ctx)
    enforce_failure_budget(
        ctx.config.raw, unclassified_count, content_span_count, manuscript.manifestation_id
    )
    _logger.info(
        "segmented",
        manifestation_id=manuscript.manifestation_id,
        span_count=len(manuscript.spans),
        content_page_count=sum(1 for page in manuscript.pages if page.is_content),
    )
    return manuscript


def _build_segment_context(manuscript: Manuscript, config: Config) -> _SegmentContext:
    """Parse config + manuscript metadata into the immutable segment context."""
    compiled_patterns = dict(config.compiled_patterns)
    (
        level_names,
        prefix_to_level,
        all_prefixes,
        top_level_prefixes,
        heading_stop_patterns,
    ) = parse_hierarchy_levels(config.patterns)
    attribution_regex = compiled_patterns.get("ATTRIBUTION")
    kitab_tracker: TrackerProtocol = KitabBabFaslTracker(
        _level_names=level_names,
        _prefix_to_level=prefix_to_level,
        _all_prefixes=all_prefixes,
        _top_level_prefixes=top_level_prefixes,
        _heading_stop_patterns=heading_stop_patterns,
        _attribution_re=attribution_regex,
    )
    sanad_tracker: TrackerProtocol = SanadMatnTracker(
        _hadith_behavior_id=HADITH__BEHAVIOR_TRANSMISSION
    )
    orchestrator = TrackerOrchestrator([kitab_tracker, sanad_tracker])
    toc = manuscript.metadata.get("toc", [])
    toc_pattern_ids = config.raw.get("toc_sections", {}).get("content_start_patterns", [])
    toc_patterns = [compiled_patterns[pid] for pid in toc_pattern_ids if pid in compiled_patterns]
    return _SegmentContext(
        config=config,
        compiled_patterns=compiled_patterns,
        behavior_rules=parse_behavior_rules(config.behaviors),
        start_thresholds=parse_start_thresholds(config.patterns),
        orchestrator=orchestrator,
        boundary_regex=compile_boundary_splitter(config.patterns),
        heading_disqualifiers=parse_heading_disqualifiers(config.patterns),
        heading_qualifiers=parse_heading_qualifiers(config.patterns),
        narrative_genres=frozenset(config.raw.get("narrative_genres", {}).get("book_types", [])),
        attribution_regex=attribution_regex,
        attribution_strong_regex=compiled_patterns.get("ATTRIBUTION_STRONG"),
        inline_heading_regex=build_inline_heading_re(config.patterns),
        heading_marker_regex=compiled_patterns.get(HADITH__PATTERN_HEADING_MARKER),
        toc=toc,
        content_start_page=find_content_start_page(toc, toc_patterns),
        name_prefix_tokens=frozenset(
            config.raw.get("cross_page_repair", {}).get("name_prefix_tokens", [])
        ),
    )


def _build_paragraphs(
    content_pages: list[ManuscriptPage], ctx: _SegmentContext
) -> _ParagraphLayout:
    """Build the merged, heading-split paragraph list plus page footnotes."""
    combined_text, page_starts, pages_list = build_combined_text(
        content_pages, ctx.name_prefix_tokens, _NAME_CONTINUATION_REGEX
    )
    page_footnotes: dict[int, dict[str, str]] = {}
    for page in content_pages:
        if page.footnote:
            page_footnotes[page.page_number] = split_footnote_entries_to_dict(page.footnote)
    toc_anchors = find_toc_anchors(combined_text, ctx.toc, page_starts, pages_list)
    paragraphs_with_anchors = split_with_page_tracking(
        combined_text,
        SplitLayout(
            ctx.boundary_regex,
            page_starts,
            pages_list,
            ctx.config.thresholds.min_span_chars,
            toc_anchors,
        ),
    )
    paragraphs = [(text, pg_start, pg_end) for text, pg_start, pg_end, _ in paragraphs_with_anchors]
    anchor_by_key = {
        (text, pg_start, pg_end): anchor
        for text, pg_start, pg_end, anchor in paragraphs_with_anchors
        if anchor is not None
    }
    paragraphs = _merge_isnad_splits(paragraphs, ctx)
    paragraphs = _split_headings(paragraphs, ctx)
    return _ParagraphLayout(paragraphs, anchor_by_key, page_footnotes)


def _merge_isnad_splits(
    paragraphs: list[tuple[str, int, int]], ctx: _SegmentContext
) -> list[tuple[str, int, int]]:
    """Rejoin paragraphs where an attribution verb continues an isnad chain."""
    cues = build_merge_cues(
        ctx.config.raw,
        ctx.config.patterns,
        ctx.attribution_regex,
        ctx.attribution_strong_regex,
        ctx.config.thresholds,
    )
    return merge_isnad_continuations(paragraphs, cues)


def _split_headings(
    paragraphs: list[tuple[str, int, int]], ctx: _SegmentContext
) -> list[tuple[str, int, int]]:
    """Split heading markers and inline headings from their following content."""
    min_heading_chars = ctx.config.thresholds.heading_split_min_heading_chars
    if ctx.inline_heading_regex is not None and ctx.attribution_strong_regex is not None:
        max_heading_chars = ctx.config.thresholds.heading_split_max_heading_chars
        paragraphs = split_at_inline_headings(
            paragraphs,
            HeadingCues(
                ctx.inline_heading_regex,
                ctx.attribution_strong_regex,
                min_heading_chars,
                ctx.name_prefix_tokens,
                max_heading_chars,
            ),
        )
    if ctx.heading_marker_regex is not None and ctx.attribution_strong_regex is not None:
        paragraphs = split_heading_from_content(
            paragraphs,
            ctx.heading_marker_regex,
            ctx.attribution_strong_regex,
            min_heading_chars,
        )
    return paragraphs


def _emit_spans(
    manuscript: Manuscript, layout: _ParagraphLayout, ctx: _SegmentContext
) -> tuple[int, int]:
    """Append one Span per paragraph; return (unclassified_count, content_span_count)."""
    unclassified_count = 0
    content_span_count = 0
    prev_span_id: str | None = None
    prev_hadith_span_id: str | None = None
    book_type = manuscript.metadata.get("book_type")
    for span_index, (paragraph_text, page_start, page_end) in enumerate(layout.paragraphs):
        span_id = HADITH__SPAN_ID_FORMAT.format(
            manifestation_id=manuscript.manifestation_id, index=span_index
        )
        detected = detect_patterns(paragraph_text, ctx.compiled_patterns)
        detected = filter_heading_disqualifiers(paragraph_text, detected, ctx.heading_disqualifiers)
        detected = filter_heading_shape(paragraph_text, detected, ctx.heading_qualifiers)
        detected = drop_heading_for_narrative(
            paragraph_text,
            detected,
            ctx.config.thresholds.narrative_heading_max_chars,
            ctx.narrative_genres,
            book_type,
        )
        behavior, routed_explicitly = route_behavior(
            detected, ctx.behavior_rules, ctx.start_thresholds, book_type
        )
        if not routed_explicitly:
            unclassified_count += 1
        content_span_count += 1
        if ctx.content_start_page is not None and page_end < ctx.content_start_page:
            behavior = HADITH__BEHAVIOR_EDITORIAL_FRONTMATTER
        ctx.orchestrator.advance(behavior, paragraph_text, span_id)
        hierarchy = ctx.orchestrator.current_path()
        footnote_entries = _collect_footnotes(layout.page_footnotes, page_start, page_end)
        anchor = layout.anchor_by_key.get((paragraph_text, page_start, page_end))
        metadata = _build_span_metadata(
            behavior, detected, anchor, prev_span_id, prev_hadith_span_id
        )
        manuscript.spans.append(
            Span(
                span_id=span_id,
                text=paragraph_text,
                page_start=page_start,
                page_end=page_end,
                span_type=HADITH__SPAN_TYPE_PARAGRAPH,
                patterns=detected,
                behavior=behavior,
                hierarchy=hierarchy,
                footnote_text=attach_footnote_text(paragraph_text, footnote_entries),
                metadata=metadata,
            )
        )
        prev_span_id = span_id
        if behavior == HADITH__BEHAVIOR_TRANSMISSION:
            prev_hadith_span_id = span_id
    return unclassified_count, content_span_count


def _build_span_metadata(
    behavior: str,
    detected_patterns: list[Pattern],
    anchor: TocAnchor | None,
    prev_span_id: str | None,
    prev_hadith_span_id: str | None,
) -> dict[str, Any]:
    """Build the per-span metadata dict: cross-references plus TOC anchor fields."""
    metadata: dict[str, Any] = {}
    if behavior == "AUTHOR_COMMENTARY" and prev_span_id is not None:
        metadata["refers_to_span_id"] = prev_span_id
    if behavior == HADITH__BEHAVIOR_TRANSMISSION:
        has_back_ref = any(pattern.pattern_id == "ISNAD_BACK_REF" for pattern in detected_patterns)
        if has_back_ref and prev_hadith_span_id is not None:
            metadata["isnad_back_ref"] = True
            metadata["refers_to_span_id"] = prev_hadith_span_id
    if anchor is not None:
        metadata["toc_title"] = anchor.title
        metadata["toc_level"] = anchor.level
        metadata["toc_page_number"] = anchor.page_number
    return metadata


def _collect_footnotes(
    page_footnotes: dict[int, dict[str, str]], page_start: int, page_end: int
) -> dict[str, str]:
    """Merge footnote entries across a span's inclusive page range."""
    entries: dict[str, str] = {}
    for page_number in range(page_start, page_end + 1):
        entries.update(page_footnotes.get(page_number, {}))
    return entries
