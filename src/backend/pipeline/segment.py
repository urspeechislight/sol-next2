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

Ported from sol-next's src/phases/segment.py; the routing table and the
pattern-detection / heading split were once shards under the old file-size cap
and now live here with the orchestrator. The quran-corpus pattern augmentation
is omitted (the quran service is not wired in this milestone); the routing
table reaches GENERAL_PROSE directly. Every compiled pattern comes from
the central backend.patterns module; this module imports no regex machinery.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from backend.core.logging import get_logger
from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.boundaries import build_merge_cues, merge_isnad_continuations
from backend.pipeline.boundaries_headings import (
    HeadingCues,
    build_inline_heading_re,
    split_at_inline_headings,
)
from backend.pipeline.config import Config
from backend.pipeline.contracts import validate_manuscript_for_phase
from backend.pipeline.errors import SegmentError
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
from backend.pipeline.toc_alignment import (
    AnchoredParagraph,
    TocAnchor,
    find_toc_anchors,
)
from backend.pipeline.trackers import TrackerOrchestrator, TrackerProtocol
from backend.pipeline.trackers.kitab_bab_fasl import KitabBabFaslTracker, parse_hierarchy_levels
from backend.pipeline.trackers.sanad_matn import SanadMatnTracker
from backend.pipeline.trackers.toc_hierarchy import TocHierarchyTracker
from backend.pipeline.vocab import (
    HADITH__BEHAVIOR_EDITORIAL_FRONTMATTER,
    HADITH__BEHAVIOR_GENERAL_PROSE,
    HADITH__BEHAVIOR_SECTION_HEADING,
    HADITH__BEHAVIOR_TRANSMISSION,
    HADITH__PATTERN_HEADING_MARKER,
    HADITH__SPAN_TYPE_PARAGRAPH,
    HADITH__SUBSECTION_HEADING_MAX_CHARS,
)

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

    paragraphs: list[AnchoredParagraph]
    anchor_by_index: dict[int, TocAnchor]
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
    toc = manuscript.metadata.get("toc", [])
    hierarchy_tracker: TrackerProtocol = (
        TocHierarchyTracker()
        if toc
        else KitabBabFaslTracker(
            _level_names=level_names,
            _prefix_to_level=prefix_to_level,
            _all_prefixes=all_prefixes,
            _top_level_prefixes=top_level_prefixes,
            _heading_stop_patterns=heading_stop_patterns,
            _attribution_re=attribution_regex,
        )
    )
    sanad_tracker: TrackerProtocol = SanadMatnTracker(
        _hadith_behavior_id=HADITH__BEHAVIOR_TRANSMISSION
    )
    orchestrator = TrackerOrchestrator([hierarchy_tracker, sanad_tracker])
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
    paragraphs = _merge_isnad_splits(paragraphs_with_anchors, ctx)
    paragraphs = _split_headings(paragraphs, ctx)
    anchor_by_index = {
        index: anchor for index, (_, _, _, anchor) in enumerate(paragraphs) if anchor is not None
    }
    return _ParagraphLayout(paragraphs, anchor_by_index, page_footnotes)


def _merge_isnad_splits(
    paragraphs: list[AnchoredParagraph], ctx: _SegmentContext
) -> list[AnchoredParagraph]:
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
    paragraphs: list[AnchoredParagraph], ctx: _SegmentContext
) -> list[AnchoredParagraph]:
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
    for span_index, (paragraph_text, page_start, page_end, _) in enumerate(layout.paragraphs):
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
        anchor = layout.anchor_by_index.get(span_index)
        ctx.orchestrator.advance(behavior, paragraph_text, span_id, anchor)
        hierarchy = ctx.orchestrator.current_path()
        footnote_entries = _collect_footnotes(layout.page_footnotes, page_start, page_end)
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


_SUBSECTION_HEADING_LINE_REGEX: CompiledPattern = cached_compile(
    rf"^\*\s+([^\n]{{2,{HADITH__SUBSECTION_HEADING_MAX_CHARS}}})\n"
)


def detect_patterns(text: str, compiled_patterns: dict[str, CompiledPattern]) -> list[Pattern]:
    """Run all compiled pattern detectors against a span's text.

    Every regex match produces a Pattern object carrying its matched slice and
    character offsets, so later phases can build evidence anchors from it.
    """
    detected: list[Pattern] = []
    for pattern_id, compiled_regex in compiled_patterns.items():
        for match in compiled_regex.finditer(text):
            detected.append(
                Pattern(
                    pattern_id=pattern_id,
                    matched_text=match.group(),
                    char_start=match.start(),
                    char_end=match.end(),
                )
            )
    return detected


def split_heading_from_content(
    paragraphs: list[AnchoredParagraph],
    heading_regex: CompiledPattern,
    attribution_strong_regex: CompiledPattern,
    min_heading_chars: int,
) -> list[AnchoredParagraph]:
    """Split paragraphs where a heading marker precedes attribution content.

    Two modes: a classical heading keyword (باب/كتاب/فصل) sharing a line with
    the start of a hadith chain — splits where ATTRIBUTION_STRONG begins, only
    when the heading portion is at least min_heading_chars long; and a modern
    asterisk subsection (``* X :``) on its own line followed by narrative
    content — splits at the first newline so the content gets its own behavior.
    The TOC anchor rides with the heading part, which is the paragraph opening
    it was placed on; the split-off content gets no anchor.
    """
    result: list[AnchoredParagraph] = []
    for text, page_start, page_end, anchor in paragraphs:
        subsection = _split_subsection(text, page_start, page_end, anchor)
        if subsection is not None:
            result.extend(subsection)
            continue
        heading_match = heading_regex.match(text)
        if heading_match is None:
            result.append((text, page_start, page_end, anchor))
            continue
        attr_match = attribution_strong_regex.search(text, pos=heading_match.end())
        if attr_match is None:
            result.append((text, page_start, page_end, anchor))
            continue
        heading_text = text[: attr_match.start()].rstrip()
        if len(heading_text) < min_heading_chars:
            result.append((text, page_start, page_end, anchor))
            continue
        result.append((heading_text, page_start, page_end, anchor))
        result.append((text[attr_match.start() :], page_start, page_end, None))
    return result


def _split_subsection(
    text: str, page_start: int, page_end: int, anchor: TocAnchor | None
) -> list[AnchoredParagraph] | None:
    """Split a ``* heading :`` subsection line from its following content.

    Returns the [heading, content] pair when the text opens with an asterisk
    subsection heading that has non-empty content after it; None otherwise. The
    anchor rides with the heading; the content gets none.
    """
    sub_match = _SUBSECTION_HEADING_LINE_REGEX.match(text)
    if sub_match is None:
        return None
    heading_text = text[: sub_match.end()].rstrip()
    stripped_content = text[sub_match.end() :].strip()
    if not stripped_content:
        return None
    return [
        (heading_text, page_start, page_end, anchor),
        (stripped_content, page_start, page_end, None),
    ]


@dataclass(frozen=True, slots=True)
class BehaviorRule:
    """A pre-parsed behavior routing rule from config."""

    behavior_id: str
    requires: frozenset[str]
    any_of: frozenset[str]
    none_of: frozenset[str]
    priority: int
    genre_gate: frozenset[str] | None = None


def parse_behavior_rules(raw_behaviors: list[dict[str, Any]]) -> list[BehaviorRule]:
    """Parse behavior routing rules from config, sorted by priority descending."""
    rules: list[BehaviorRule] = []
    for entry in raw_behaviors:
        gate_raw = entry.get("genre_gate")
        rules.append(
            BehaviorRule(
                behavior_id=entry["id"],
                requires=frozenset(entry.get("requires", [])),
                any_of=frozenset(entry.get("any_of", [])),
                none_of=frozenset(entry.get("none_of", [])),
                priority=entry.get("priority", 0),
                genre_gate=frozenset(gate_raw) if gate_raw else None,
            )
        )
    rules.sort(key=lambda rule: rule.priority, reverse=True)
    return rules


def parse_start_thresholds(raw_patterns: list[dict[str, Any]]) -> dict[str, int]:
    """Extract start_threshold values: pattern_id -> max char_start for routing.

    A start_threshold on a pattern means it only counts for behavior routing when
    its earliest match starts within that many characters of the span's start.
    """
    thresholds: dict[str, int] = {}
    for entry in raw_patterns:
        if "start_threshold" in entry:
            thresholds[entry["id"]] = int(entry["start_threshold"])
    return thresholds


def route_behavior(
    detected_patterns: list[Pattern],
    behavior_rules: list[BehaviorRule],
    start_thresholds: dict[str, int],
    book_type: str | None = None,
) -> tuple[str, bool]:
    """Route detected patterns to a behavior label via the routing table.

    Evaluates rules in priority order (highest first). A rule matches when all
    requires are present, at least one any_of is present (if non-empty), none of
    none_of are present, and genre_gate passes (if set). Returns (label,
    routed_explicitly): routed_explicitly is True when no patterns were detected
    (the clean default to GENERAL_PROSE), when the detected patterns are all ones
    the routing table references nowhere (so no rule could ever match them — a
    lone generic speech verb قال is prose, not a gap), when a configured rule
    matched, or when the only rules whose patterns matched were declined by their
    genre_gate — that last case is a deliberate genre exclusion, so GENERAL_PROSE
    is the intended answer, not a routing gap. routed_explicitly is False only
    when a rule-referenced pattern was detected and no rule matched — the genuine
    unrouted case the failure budget tracks, which the referenced-pattern test
    keeps genre-invariant so prose-dense books do not exhaust the budget.
    """
    detected_ids = _thresholded_pattern_ids(detected_patterns, start_thresholds)
    if not detected_ids:
        return HADITH__BEHAVIOR_GENERAL_PROSE, True
    if detected_ids.isdisjoint(_routing_referenced_patterns(behavior_rules)):
        return HADITH__BEHAVIOR_GENERAL_PROSE, True
    genre_excluded_match = False
    for rule in behavior_rules:
        if not rule.requires and not rule.any_of:
            continue
        if rule.requires and not rule.requires.issubset(detected_ids):
            continue
        if rule.any_of and not rule.any_of.intersection(detected_ids):
            continue
        if rule.none_of and rule.none_of.intersection(detected_ids):
            continue
        if rule.genre_gate is not None and (book_type is None or book_type not in rule.genre_gate):
            genre_excluded_match = True
            continue
        return rule.behavior_id, True
    if genre_excluded_match:
        return HADITH__BEHAVIOR_GENERAL_PROSE, True
    _logger.warning(
        "no-behavior-rule-matched",
        pattern_ids=sorted(detected_ids),
        behavior=HADITH__BEHAVIOR_GENERAL_PROSE,
    )
    return HADITH__BEHAVIOR_GENERAL_PROSE, False


def _routing_referenced_patterns(behavior_rules: list[BehaviorRule]) -> frozenset[str]:
    """Every pattern id the routing table references, in requires, any_of, or none_of.

    A pattern the table names nowhere cannot make any rule match or fail to
    match, so a span carrying only such patterns routes to GENERAL_PROSE as the
    intended answer, not an unrouted gap. Deriving this set from the rules keeps
    it correct as the table changes and keeps the failure budget genre-invariant:
    a generic speech verb (قال) or a rijal-grading term detected in grammar or
    history prose is not a routing signal, so prose density does not exhaust the
    budget the way a hadith book's unrouted isnad combinations legitimately do.
    """
    referenced: set[str] = set()
    for rule in behavior_rules:
        referenced |= rule.requires
        referenced |= rule.any_of
        referenced |= rule.none_of
    return frozenset(referenced)


def _thresholded_pattern_ids(
    detected_patterns: list[Pattern], start_thresholds: dict[str, int]
) -> set[str]:
    """Apply start_thresholds and return the pattern ids eligible for routing."""
    if not start_thresholds:
        return {pattern.pattern_id for pattern in detected_patterns}
    earliest: dict[str, int] = {}
    for pattern in detected_patterns:
        if pattern.pattern_id not in earliest or pattern.char_start < earliest[pattern.pattern_id]:
            earliest[pattern.pattern_id] = pattern.char_start
    eligible: set[str] = set()
    for pattern_id, position in earliest.items():
        threshold = start_thresholds.get(pattern_id)
        if threshold is not None and position > threshold:
            continue
        eligible.add(pattern_id)
    return eligible


def validate_required_behaviors(raw_behaviors: list[dict[str, Any]]) -> None:
    """Validate that segment's built-in behavior ids exist in config.

    Segment references GENERAL_PROSE and SECTION_HEADING by name. If either is
    missing from config, routing and hierarchy tracking malfunction.

    Raises SegmentError if a required behavior id is missing from config.
    """
    behavior_ids = {entry["id"] for entry in raw_behaviors}
    required = {HADITH__BEHAVIOR_GENERAL_PROSE, HADITH__BEHAVIOR_SECTION_HEADING}
    missing = required - behavior_ids
    if missing:
        raise SegmentError(
            f"Config missing behavior ids {sorted(missing)}; segment needs {sorted(required)}"
        ) from None
