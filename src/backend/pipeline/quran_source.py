"""Build the Qurʾān as a manifestation for the extraction pipeline.

The corpus books reach the pipeline as pages of prose that segment must divide
into spans; the Qurʾān's structure is already given, so this module maps it
directly: one QURAN_VERSE span per canonical āyah, grouped under its sūra in the
hierarchy. The 112 repeated basmalas (stored at āyah key "0") are dropped — they
carry no named entity and would inflate the corpus 112-fold — leaving exactly the
6,236 canonical āyāt. Each span carries the verse's CAMeL morphology (a committed
build input) in metadata, which the entity extractor reads to disambiguate names
and which feeds the graph's root/lemma layer.

Because the spans already carry behavior + hierarchy, the segment phase is
skipped and the shared ``extract`` phase runs directly: it atomizes each verse
into a QURAN_UNIT and runs ``quran_entity_extractor`` to name the entities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.core.constants import QURAN__MANIFESTATION_ID
from backend.pipeline.config import Config
from backend.pipeline.extract import extract
from backend.pipeline.models import HierarchyPath, Manuscript, ManuscriptPage, Span

QURAN__WORK_ID: str = QURAN__MANIFESTATION_ID

_BEHAVIOR_VERSE: str = "QURAN_VERSE"
_SPAN_TYPE: str = "VERSE"
_BASMALA_KEY: str = "0"
_ARABIC_KEY: str = "ar"
_VERSES_KEY: str = "verses"


def _surah_hierarchy(surah_number: str) -> HierarchyPath:
    """The one-level hierarchy locating a verse in its sūra."""
    return HierarchyPath(path=[f"سورة {surah_number}"], path_ids=[f"surah:{surah_number}"], depth=1)


def _verse_span(
    surah_number: str, ayah_number: str, verse: dict[str, Any], morphology: list[dict[str, Any]]
) -> Span:
    """One QURAN_VERSE span for a canonical āyah, carrying its morphology in metadata."""
    metadata: dict[str, Any] = {
        "book_type": QURAN__MANIFESTATION_ID,
        "surah": int(surah_number),
        "ayah": int(ayah_number),
        "morphology": morphology,
    }
    return Span(
        span_id=f"quran:{surah_number}:{ayah_number}",
        text=verse[_ARABIC_KEY],
        page_start=int(surah_number),
        page_end=int(surah_number),
        span_type=_SPAN_TYPE,
        behavior=_BEHAVIOR_VERSE,
        hierarchy=_surah_hierarchy(surah_number),
        metadata=metadata,
    )


def build_quran_manuscript(quran_path: Path, morphology_path: Path, config: Config) -> Manuscript:
    """Assemble the Qurʾān manifestation and run it through the extract phase.

    Reads the curated ``quran.json`` and the committed per-verse morphology,
    builds one QURAN_VERSE span per canonical āyah (skipping the basmala at key
    "0"), and returns the extracted Manuscript with entities + units populated.
    """
    quran = json.loads(quran_path.read_text(encoding="utf-8"))
    morphology = json.loads(morphology_path.read_text(encoding="utf-8"))
    spans: list[Span] = []
    pages: list[ManuscriptPage] = []
    for surah_number, surah in quran.items():
        verses = surah[_VERSES_KEY]
        ayah_texts: list[str] = []
        for ayah_number, verse in verses.items():
            if ayah_number == _BASMALA_KEY:
                continue
            ref = f"{surah_number}:{ayah_number}"
            spans.append(_verse_span(surah_number, ayah_number, verse, morphology.get(ref, [])))
            ayah_texts.append(verse[_ARABIC_KEY])
        pages.append(
            ManuscriptPage(
                page_number=int(surah_number),
                page_name=f"سورة {surah_number}",
                text="\n".join(ayah_texts),
            )
        )
    manuscript = Manuscript(
        work_id=QURAN__WORK_ID,
        manifestation_id=QURAN__MANIFESTATION_ID,
        pages=pages,
        spans=spans,
        metadata={"book_type": QURAN__MANIFESTATION_ID},
    )
    return extract(manuscript, config)
