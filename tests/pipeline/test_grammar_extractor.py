"""Tests for the grammar-marker extractor (iʿrāb / naḥw / ṣarf terms).

The fixture is a sentence from a grammar exposition that names a case, a
morphophonemic operation, a syntactic role, and a verb form; the extractor must
emit one categorized GRAMMAR_TERM entity per marker, and nothing at all for a
book outside the configured grammar genres.
"""

from __future__ import annotations

from backend.pipeline.config import load_config
from backend.pipeline.extractors.grammar import grammar_term_extractor
from backend.pipeline.models import HierarchyPath, Span

_CFG = load_config()
_GRAMMAR_GENRE = "arabic-language-sciences"
_TEXT = "المضارع المرفوع علامته الضمّة ويجب الإدغام في الفاعل ووزن الفعل مبنيّ"


def _span(book_type: str | None) -> Span:
    metadata = {"book_type": book_type} if book_type is not None else {}
    return Span(
        span_id="s_grammar",
        text=_TEXT,
        page_start=1,
        page_end=1,
        span_type="paragraph",
        behavior="GENERAL_PROSE",
        hierarchy=HierarchyPath(path=["فصل"], path_ids=["f1"], depth=1),
        metadata=metadata,
    )


def test_should_extract_categorized_grammar_terms() -> None:
    """Each marker (with its clitic/article) becomes a categorized GRAMMAR_TERM."""
    entities = grammar_term_extractor(_span(_GRAMMAR_GENRE), _CFG)
    by_text = {e.text: e.metadata["category"] for e in entities}
    assert by_text.get("المضارع") == "sarf_verbform"
    assert by_text.get("المرفوع") == "irab_case"
    assert by_text.get("الضمّة") == "irab_mark"
    assert by_text.get("الإدغام") == "sarf_op"
    assert by_text.get("الفاعل") == "nahw_role"
    assert by_text.get("ووزن") == "sarf_pattern"
    assert by_text.get("مبنيّ") == "word_class"


def test_should_normalize_the_article_into_a_lemma() -> None:
    """The lemma drops a leading article so الX variants group; a bare root stays whole."""
    entities = grammar_term_extractor(_span(_GRAMMAR_GENRE), _CFG)
    lemma = {e.text: e.metadata["lemma"] for e in entities}
    assert lemma["المرفوع"] == "مرفوع"
    assert lemma["الفاعل"] == "فاعل"
    assert lemma["الإدغام"] == "إدغام"
    assert lemma["ووزن"] == "ووزن"


def test_should_anchor_each_term_to_its_exact_offsets() -> None:
    """Every entity's char window reproduces its text exactly."""
    entities = grammar_term_extractor(_span(_GRAMMAR_GENRE), _CFG)
    assert entities
    for entity in entities:
        assert _TEXT[entity.char_start : entity.char_end] == entity.text


def test_should_extract_nothing_outside_grammar_genres() -> None:
    """A hadith or history book yields no grammar terms even with matching words."""
    assert grammar_term_extractor(_span("shia-hadith-general"), _CFG) == []
    assert grammar_term_extractor(_span(None), _CFG) == []
