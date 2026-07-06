"""Grammatical-marker extractor for Arabic morphology and syntax works (Phase 3).

The narrator/mention extractors model a hadith's chain; a grammar treatise like
the Kanāsh carries no chain but is dense with the technical vocabulary of naḥw
(syntax), ṣarf (morphology), and iʿrāb (inflection). This extractor emits one
GRAMMAR_TERM entity per marker occurrence, categorized (case, mark, role, verb
form, pattern, morphophonemic operation, governing operator, word class), so the
graph can be queried by grammatical concept — every passage that discusses النصب,
every span that names a وزن, every mention of a مبتدأ.

It is genre-scoped: it runs only on books whose category is in
``grammar_extraction.genres`` (Arabic-language sciences by default). That scope
is what lets the term regexes stay inclusive — نصب, جر, حذف read as their
grammatical senses across a grammar volume, not as "erect", "pull", "delete",
which would make the same words treacherous in a hadith or history book.

Each term regex is clitic-aware: Arabic attaches a leading conjunction or
preposition (و ف ب ك ل) and the definite article (ال) to a word, so ``_CLITIC``
allows them at the match start (pinned there by a lookbehind so a term is never
matched mid-word) and ``_END`` stops before the next Arabic letter so an
inflected suffix is matched whole or not at all. The surface form is the entity
text (offset-exact); ``_lemma`` strips a leading article to a base form stored in
metadata, so the graph can group الوزن / والوزن / وزن under one concept.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from backend.core.constants import ENTITY__CATEGORY_KEY, GRAMMAR__ENTITY_TERM
from backend.patterns import CompiledPattern, cached_compile
from backend.pipeline.contracts import PHASE_CONTRACTS
from backend.pipeline.models import Entity, Span, create_entity

if TYPE_CHECKING:
    from backend.pipeline.config import Config

GRAMMAR__LEMMA_KEY: Final[str] = "lemma"

_CLITIC: Final[str] = r"(?<![ء-ي])[وفبكل]?"
_END: Final[str] = r"(?![ء-ي])"
_STRIP_ARTICLE: Final[CompiledPattern] = cached_compile(r"^[وفبكل]?ال")

_IRAB_CASE: Final[CompiledPattern] = cached_compile(
    rf"{_CLITIC}(?:ال)?(?:مرفوع|منصوب|مجرور|مجزوم)(?:ة|ان|ين|ون|ات)?{_END}"
    rf"|{_CLITIC}ال(?:رفع|نصب|جرّ|جر|جزم){_END}"
)
_IRAB_MARK: Final[CompiledPattern] = cached_compile(
    rf"{_CLITIC}ال(?:ضمّة|ضمة|فتحة|كسرة|سكون|تنوين){_END}|علامة الإعراب"
)
_NAHW_ROLE: Final[CompiledPattern] = cached_compile(
    rf"{_CLITIC}(?:ال)?(?:مبتدأ|خبر|فاعل|مفعول(?: به| فيه| له| معه| مطلق)?"
    rf"|حال|تمييز|نعت|بدل|مضاف(?: إليه)?|معطوف|توكيد|منادى){_END}|نائب الفاعل"
)
_SARF_VERBFORM: Final[CompiledPattern] = cached_compile(
    rf"{_CLITIC}(?:ال)?(?:ماضي|مضارع|أمر|مصدر){_END}"
    r"|اسم (?:الفاعل|المفعول|التفضيل|المرّة|المرة|الهيئة|الآلة|الزمان|المكان)"
    r"|الصفة المشبّهة|الصفة المشبهة"
)
_SARF_PATTERN: Final[CompiledPattern] = cached_compile(
    rf"{_CLITIC}(?:ال)?(?:وزن|صيغة|أبنية|ميزان){_END}"
    r"|(?:فاء|عين|لام) (?:الفعل|الكلمة)"
    rf"|{_CLITIC}ال(?:ثلاثيّ|ثلاثي|رباعيّ|رباعي|خماسيّ|خماسي|مجرّد|مجرد|مزيد){_END}"
)
_SARF_OP: Final[CompiledPattern] = cached_compile(
    rf"{_CLITIC}ال(?:إدغام|إعلال|إبدال|إمالة){_END}|القلب المكانيّ|القلب المكاني|حروف الزيادة"
)
_OPERATOR: Final[CompiledPattern] = cached_compile(
    rf"{_CLITIC}(?:ال)?(?:عامل|معمول|ناصب|جازم|رافع|خافض){_END}"
    rf"|{_CLITIC}ال(?:نواصب|جوازم){_END}"
    rf"|{_CLITIC}(?:ينصب|يرفع|يجزم|يجرّ|يجر|تنصب|ترفع|تجزم|تجرّ){_END}"
)
_WORD_CLASS: Final[CompiledPattern] = cached_compile(
    rf"{_CLITIC}(?:ال)?(?:معرب|مبنيّ|مبني|منصرف){_END}|ممنوع من الصرف"
    rf"|{_CLITIC}ال(?:نكرة|معرفة|ضمير|موصول|مثنّى|مثنى){_END}"
)

_CATEGORIES: Final[tuple[tuple[str, CompiledPattern], ...]] = (
    ("irab_case", _IRAB_CASE),
    ("irab_mark", _IRAB_MARK),
    ("nahw_role", _NAHW_ROLE),
    ("sarf_verbform", _SARF_VERBFORM),
    ("sarf_pattern", _SARF_PATTERN),
    ("sarf_op", _SARF_OP),
    ("operator", _OPERATOR),
    ("word_class", _WORD_CLASS),
)


def grammar_term_extractor(span: Span, config: Config) -> list[Entity]:
    """Emit a GRAMMAR_TERM entity per grammatical marker in a grammar-genre span.

    Returns [] for any book whose category is not in the configured grammar
    genres, so the term regexes run only where their grammatical sense holds.
    Each category is scanned; overlapping matches keep the earliest category, so
    a position yields at most one term. Offsets index the span text exactly.
    """
    genres = frozenset(config.raw.get("grammar_extraction", {}).get("genres", []))
    if not genres or span.metadata.get("book_type") not in genres:
        return []
    claimed: dict[int, tuple[int, str]] = {}
    for category, regex in _CATEGORIES:
        for match in regex.finditer(span.text):
            start = match.start()
            if start in claimed:
                continue
            claimed[start] = (match.end(), category)
    phase = PHASE_CONTRACTS["extract"].phase_number
    entities: list[Entity] = []
    for start in sorted(claimed):
        end, category = claimed[start]
        surface = span.text[start:end]
        entities.append(
            create_entity(
                entity_type=GRAMMAR__ENTITY_TERM,
                text=surface,
                char_start=start,
                char_end=end,
                span=span,
                extractor_id="grammar_term_extractor",
                config=config,
                phase=phase,
                metadata={ENTITY__CATEGORY_KEY: category, GRAMMAR__LEMMA_KEY: _lemma(surface)},
            )
        )
    return entities


def _lemma(surface: str) -> str:
    """The base term: the surface form with a leading article removed.

    Only a clitic that precedes the definite article ال is stripped
    (الوزن/والوزن/بالفاعل), which is unambiguous. A bare leading conjunction is
    left in place, because a single و or ب may be part of the root (وزن, بدل)
    and stripping it would fabricate a false lemma (زن, دل)."""
    return _STRIP_ARTICLE.sub("", surface, count=1)
