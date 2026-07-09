"""Decompose a Mizan al-I'tidal entry head into classical Arabic name parts.

Each biographical entry opens with the narrator's name before the critical
prose begins. This module splits that opening into the five onomastic
components scholars use to tell apart two narrators who share a lineage:

* ``ism``   the given name, possibly compound (``عبد الله``); empty when the
            person is known only by a kunya.
* ``nasab`` the ordered ancestor chain, one element per ``بن``/``ابن`` link,
            with the link word stripped.
* ``kunya`` the ``أبو``/``أم`` teknonym, if any.
* ``nisba`` relational attributions (place, tribe, school): ``الكوفي``,
            ``السكوني``, ``الهاشمي``.
* ``laqab`` titles, epithets, and professions: ``الحافظ``, ``الإمام``,
            ``النحاس``, ``العطار``.

The parser walks name tokens greedily and stops at the first token that opens
biography (a narration verb, a grading term, a date), so the classification
patterns compile through :func:`backend.patterns.cached_compile` (CENTRAL-002)
and the boundary never runs into the prose. Bracketed transmitter symbols
(``[م ، د]``) and inline footnote markers (``(2)``) are removed first and the
symbols are returned separately.
"""

from __future__ import annotations

from typing import Any

from backend.patterns import cached_compile

_SIGLA_RE = cached_compile(r"\[([^\]]*)\]")
_FOOTNOTE_RE = cached_compile(r"\(\s*\d+\s*\)")
_SEPARATORS_RE = cached_compile(r"[/\\،؛]")
_WHITESPACE_RE = cached_compile(r"\s+")
_NISBA_SUFFIX_RE = cached_compile(r"(?:ي|ية|اني|وي|يه)$")

_NASAB_LINK = frozenset({"بن", "ابن", "بنت"})
_KUNYA_HEAD = frozenset({"أبو", "أبي", "أبا", "أم", "ابو", "ابى", "ابا", "أمة"})
_THEOPHORIC_HEAD = frozenset({"عبد", "عبيد", "عبده"})
_ARTICLE = "ال"
_RELOCATION = "ثم"

_BIO_MARKERS = frozenset({
    "عن", "روى", "يروي", "روي", "حدث", "حدثنا", "سمع", "أخذ", "قال", "وقال",
    "وثقه", "ضعفه", "تركه", "كذبه", "مات", "توفي", "ولد", "أحد", "من", "هو",
    "وهو", "له", "عداده", "صاحب", "شيخ", "نزيل", "ذكره", "أورده", "متروك",
    "ثقة", "صدوق", "ضعيف", "مجهول", "لا", "كان", "يعرف", "ويعرف", "قيل",
    "وقيل", "فيه", "منكر", "الذي", "شيعي", "طوف", "حكى", "جاء", "يحدث",
    "سكن", "قدم", "رحل", "لقي", "عرف", "يكنى", "أدرك", "له.",
})

_LAQAB_WORDS = frozenset({
    "الحافظ", "الامام", "الإمام", "القاضي", "الزاهد", "العطار", "الأحمر",
    "الضرير", "النحاس", "الحاكم", "الشيخ", "الفقيه", "المقرئ", "الواعظ",
    "الأعور", "الأعمى", "الصغير", "الكبير", "الأكبر", "الأصغر", "المحدث",
    "الخطيب", "الوزير", "الأعرج", "الأمير", "الزيات", "الوراق", "الصائغ",
    "البزاز", "الحداد", "النساج", "الجمال", "الطحان", "العابد", "الخزاز",
    "الأعمش", "الأحول", "الضبعي", "المؤدب", "الملقب", "الكاتب", "التاجر",
})


def strip_markers(head: str) -> tuple[str, list[str]]:
    """Return (clean_text, sigla) with footnotes and ``[..]`` symbols removed."""
    sigla = [g.strip() for g in _SIGLA_RE.findall(head) if g.strip()]
    text = _SIGLA_RE.sub(" ", head)
    text = _FOOTNOTE_RE.sub(" ", text)
    text = _SEPARATORS_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip(), sigla


def _classify_article(tok: str) -> str:
    """Return ``'laqab'`` or ``'nisba'`` for a definite-article descriptor."""
    if tok in _LAQAB_WORDS:
        return "laqab"
    if _NISBA_SUFFIX_RE.search(tok):
        return "nisba"
    return "laqab"


def _is_article_word(tok: str) -> bool:
    """True for a definite-article descriptor that can belong to a name."""
    return tok.startswith(_ARTICLE) and len(tok) > 2 and tok not in _BIO_MARKERS


def _name_unit(tokens: list[str], i: int) -> tuple[str, int]:
    """Consume one name unit at ``i``: a kunya (``أبو عبد الله``), a theophoric
    compound (``عبد الرحمن``), or a single word. Merges ``عبد``/``عبيد`` only
    with a following article word, so a bio word after ``عبيد`` is never eaten."""
    tok = tokens[i]
    if tok in _KUNYA_HEAD and i + 1 < len(tokens):
        tail, j = _name_unit(tokens, i + 1)
        return tok + " " + tail, j
    if tok in _THEOPHORIC_HEAD and i + 1 < len(tokens) and tokens[i + 1].startswith(_ARTICLE):
        return tok + " " + tokens[i + 1], i + 2
    return tok, i + 1


def _open_name(tokens: list[str]) -> tuple[str, str, int]:
    """Return (ism, kunya, next_index) for the leading name unit."""
    if not tokens:
        return "", "", 0
    unit, i = _name_unit(tokens, 0)
    if tokens[0] in _KUNYA_HEAD:
        return "", unit, i
    return unit, "", i


def decompose(head: str) -> dict[str, Any]:
    """Decompose a raw entry head into ism/nasab/kunya/nisba/laqab plus name."""
    text, sigla = strip_markers(head)
    tokens = text.split()
    ism, kunya, i = _open_name(tokens)
    nasab: list[str] = []
    nisba: list[str] = []
    laqab: list[str] = []
    while i < len(tokens):
        tok = tokens[i]
        if tok in _NASAB_LINK and i + 1 < len(tokens):
            element, i = _name_unit(tokens, i + 1)
            nasab.append(element)
            continue
        if tok in _KUNYA_HEAD and not kunya and i + 1 < len(tokens):
            kunya, i = _name_unit(tokens, i)
            continue
        if tok == _RELOCATION and i + 1 < len(tokens) and _is_article_word(tokens[i + 1]):
            i += 1
            continue
        if _is_article_word(tok):
            bucket = nisba if _classify_article(tok) == "nisba" else laqab
            bucket.append(tok)
            i += 1
            continue
        break
    return {
        "ism": ism,
        "nasab": nasab,
        "kunya": kunya,
        "nisba": nisba,
        "laqab": laqab,
        "name": " ".join(tokens[:i]),
        "sigla": sigla,
    }
