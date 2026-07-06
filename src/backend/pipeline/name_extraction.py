"""Canonical person-name cleanup pipeline.

extract_person_name trims and cleans a text slice into a person-name
candidate: a boundary-regex crop (skipping footnote-marker parens) followed by
clean_name_text (footnote-marker replacement + trailing-punctuation strip).
Ported from sol-next's src/utils/name_extraction.py and names.py, cut down to
the path the hadith narrator extractor exercises; the compound-prefix
extension, dangling-connector strip, leading-clitic strip, end-position crop,
and the kunya/laqab/sentence-start helpers return with the biography and
rijal extractors that consume them. This module knows nothing about Pattern
or Span, by design. Every regex compiles through the central backend.patterns
module.
"""

from __future__ import annotations

from backend.patterns import (
    HONORIFIC_SIGNS,
    NAME_LEADING_PARTICLE,
    WHITESPACE,
    CompiledPattern,
    cached_compile,
    strip_tashkeel,
)
from backend.pipeline.text import is_footnote_marker_opening, replace_footnote_markers

_NAME_TRAILING_PUNCT_REGEX: CompiledPattern = cached_compile(r"[\s،,:.\-]+$")
_NAME_LIST_SEPARATOR_REGEX: CompiledPattern = cached_compile(
    r"(?:\s*[،؛,]|\s+(?:عن|قالوا|قالت|قالا|قال|كانت|كان|أنه|انه|إنه|حدثه|يقول|لما)\s).*$"
)
_NAME_HONORIFIC_TAIL_REGEX: CompiledPattern = cached_compile(r"[" + HONORIFIC_SIGNS + r"][\s\S]*$")


def clean_name_text(name: str) -> str:
    """Remove footnote markers, cut at the first honorific, normalize whitespace,
    strip a leading connective run, then strip trailing punctuation.

    Inline footnote references like (2) sit between name tokens; replacing them
    with a space keeps the tokens separated. An honorific ligature sign (﵇ ﵈ ﷺ)
    is a salutation printed after a COMPLETE name, so the first one ends the
    candidate: everything from the sign onward is dropped, which both removes
    the sign itself and cuts any prose the slice ran into past it. Internal
    whitespace is then collapsed so a print-column line break inside a name
    (صباح بن\\nعبد الحميد) stops corrupting the stored name and its registry
    match. The candidate is cropped at the first list separator (، ؛ ,) or matn
    transition word (عن / قال / أنه / حدثه …): a name never spans one, so text
    after it is a following narrator or matn (X عن Y, التيمي انه سمع Y), not part
    of this name. A leading connective run (عن / في / من …) is then
    stripped because a chain connector or matn phrase captured with the name is
    not part of it (عن ابن بطة -> ابن بطة), and the trailing class strips the
    structural delimiters (: . -) that are not name tokens.
    """
    cleaned = replace_footnote_markers(name)
    cleaned = _NAME_HONORIFIC_TAIL_REGEX.sub("", cleaned)
    cleaned = WHITESPACE.sub(" ", cleaned)
    cleaned = _NAME_LIST_SEPARATOR_REGEX.sub("", cleaned)
    cleaned = NAME_LEADING_PARTICLE.sub("", cleaned)
    cleaned = _NAME_TRAILING_PUNCT_REGEX.sub("", cleaned)
    return cleaned.strip()


def has_non_name_leading_word(name: str, leading_blocklist: frozenset[str]) -> bool:
    """True when the name's first token never heads a person name.

    A candidate whose first token is a bibliographic noun (كتاب / خبر / كلام /
    باب) or a formulaic isnad-grade term (الصحيح / الموثق) is a citation or
    grading phrase that leaked past the citation-head boundary, not a name, so
    the caller drops it. Dropping a mis-bounded slice is preferred over emitting
    it as a wrong narrator (wrong is worse than absent).
    """
    if not name:
        return False
    first, _, _ = name.partition(" ")
    return first in leading_blocklist


def refine_person_name(
    name: str,
    reject_words: frozenset[str],
    leading_strip_words: frozenset[str],
    kinship_words: frozenset[str],
) -> str | None:
    """Refine a cleaned candidate into a person name, or None when it is not one.

    Leading tokens that never open a name are stripped first: a speech verb that
    ran into the name (``قال ابن شهاب`` -> ``ابن شهاب``, ``فقال ابن عباس`` ->
    ``ابن عباس``), the vocative ``يا`` (``يا ابن أخي``), or a stray conjunction.
    The result is then rejected (None) when it is not a person. A divine or title
    word never HEADS a name, so a candidate whose first token is one is dropped:
    that is ``الله`` alone, the ``رسول الله`` / ``أمير المؤمنين`` titles, and the
    matn mis-matches where a nasab shape straddled a divine word
    (``خلق الله بن آدم`` -> ``الله بن آدم``); a real theophoric name keeps its
    servant word as the head (``عبد الله``), so it survives. A candidate whose
    every token is a genealogy link or a kinship word with no proper-name core is
    also dropped (``ابن أخي``, ``عمه``). Rejecting a mis-captured slice is 'wrong
    is worse than absent'. Comparisons are tashkeel-insensitive so a vowelled
    manuscript rejects the same forms.
    """
    tokens = name.split()
    while tokens and strip_tashkeel(tokens[0]) in leading_strip_words:
        tokens = tokens[1:]
    if not tokens:
        return None
    if strip_tashkeel(tokens[0]) in reject_words:
        return None
    structural = {"بن", "ابن", "بنت", "ابنة"} | kinship_words | reject_words
    if all(strip_tashkeel(token) in structural for token in tokens):
        return None
    return " ".join(tokens)


def extract_person_name(
    text: str,
    start: int,
    end: int,
    boundary_regex: CompiledPattern,
) -> tuple[str, int, int] | None:
    """Trim and clean text[start:end] into a person-name candidate.

    Crops at the first boundary_regex hit, then applies clean_name_text.
    Returns (cleaned_text, abs_start, abs_end) referring to the absolute view
    of text, or None when the cleaned text is empty.
    """
    cropped_end = _crop_at_boundary(text, start, end, boundary_regex)
    raw = text[start:cropped_end].rstrip()
    cleaned = clean_name_text(raw)
    if not cleaned:
        return None
    return (cleaned, start, start + len(raw))


def locate_clean_name(
    text: str, region_start: int, region_end: int, clean_text: str
) -> tuple[int, int] | None:
    """Tightest ``[start, end)`` inside the region whose cleanup is ``clean_text``.

    The stored name is the cleaned form, but its char window must still bound
    the name's occurrence in the source so a consumer (graph node, reader
    highlight) can anchor it: the window skips a leading particle the cleanup
    stripped (إلى / عن) and spans an internal footnote marker the cleanup
    removed (ربعي بن (1) عبد الله), while excluding trailing connectives and
    punctuation. The window is found by locating the cleaned name's first and
    last tokens in the region, then confirmed by the round-trip
    ``clean_name_text(text[start:end]) == clean_text``; a candidate that does
    not round-trip returns None so the caller can fail loud rather than store a
    window that misrepresents the name.
    """
    if not clean_text:
        return None
    tokens = clean_text.split(" ")
    first_token, last_token = tokens[0], tokens[-1]
    start = text.find(first_token, region_start, region_end)
    if start == -1:
        return None
    end = text.rfind(last_token, start, region_end)
    if end == -1:
        return None
    end += len(last_token)
    if clean_name_text(text[start:end]) != clean_text:
        return None
    return start, end


def _crop_at_boundary(text: str, start: int, end: int, boundary_regex: CompiledPattern) -> int:
    """Return end cropped at the first boundary_regex hit in text[start:end].

    A '(' that opens a footnote marker like (1) is skipped so a footnote reference
    does not truncate the name spuriously.
    """
    text_slice = text[start:end]
    for boundary_match in boundary_regex.finditer(text_slice):
        opens_footnote = boundary_match.group() == "(" and is_footnote_marker_opening(
            text_slice, boundary_match.start()
        )
        if opens_footnote:
            continue
        return start + boundary_match.start()
    return end
