"""The pipeline's closed vocabularies and id formats.

Cross-module constants only the pipeline produces: behavior labels, pattern
ids, atomicizer strategies, span/unit/entity id formats. These lived in
serving ``core.constants`` before the pipeline owned its own package
surface. The four names the read side also consumes (``HADITH__ENTITY_PERSON``
and the unit types the manuscript repository projects into reader DTOs) stay
in ``core.constants``, because repositories must never import pipeline code:
the artifact is the only seam.
"""

from __future__ import annotations

from typing import Final

HADITH__UNIT_FOOTNOTE: Final[str] = "FOOTNOTE_UNIT"
HADITH__UNIT_ID_FORMAT: Final[str] = "{manifestation_id}_u{index:04d}"
HADITH__ENTITY_ID_FORMAT: Final[str] = "{span_id}_e{index:02d}"
HADITH__BEHAVIOR_TRANSMISSION: Final[str] = "HADITH_TRANSMISSION"
HADITH__BEHAVIOR_GENERAL_PROSE: Final[str] = "GENERAL_PROSE"
HADITH__BEHAVIOR_SECTION_HEADING: Final[str] = "SECTION_HEADING"
HADITH__BEHAVIOR_EDITORIAL_FRONTMATTER: Final[str] = "EDITORIAL_FRONTMATTER"
HADITH__SPAN_TYPE_PARAGRAPH: Final[str] = "paragraph"
HADITH__PATTERN_HEADING_MARKER: Final[str] = "HEADING_MARKER"
HADITH__PATTERN_BASMALA: Final[str] = "BASMALA"
HADITH__PATTERN_ATTRIBUTION: Final[str] = "ATTRIBUTION"
HADITH__PATTERN_NUMBERED_ENTRY: Final[str] = "NUMBERED_ENTRY"
HADITH__PATTERN_MATN_BOUNDARY_HINT: Final[str] = "MATN_BOUNDARY_HINT"
HADITH__PATTERN_SPEECH_VERB_GENERIC: Final[str] = "SPEECH_VERB_GENERIC"
HADITH__STRATEGY_WHOLE_SPAN: Final[str] = "whole_span"
HADITH__STRATEGY_SANAD_MATN: Final[str] = "sanad_matn_split"
HADITH__SUBSECTION_HEADING_MAX_CHARS: Final[int] = 200
