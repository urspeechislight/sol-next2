"""Build layer: the one registry of what is NOT a narrator name.

Rijal and history corpora carry many strings that are shaped like names but are
not: isnad and speech verbs (``سألت`` "I asked", ``حدثنا``), connective prefixes
(a ``فـ``/``وـ`` glued to a real name, ``فعبد الله``), descriptors (``مولى`` "client
of"), trailing relative pronouns (``الذي``), isnad formulas (``وبهذا الاسناد``),
honorific titles standing alone (``الشيخ``, ``السيد``), and book titles (``الأمالي
للشيخ الطوسي``). Left unfiltered they become fake person records with pooled,
mis-attributed grades.

This module centralises every such lookup table in one place (the SSOT the
corpus builder and the pipeline name extractor both validate against) and
exposes two operations over them:

  ``clean_name``     strip a leading connective/verb/title and a glued
                     ``فـ``/``وـ``, then delegate to the name grammar
                     (``decompose``), which keeps ism + nasab + kunya +
                     nisba/laqab and stops at the first biography-opening token.
  ``is_person_name`` after cleaning, reject a title/book/verb lead, a particle
                     phrase (``للـ``), or a too-short remainder.

The cleaning boundary is the name GRAMMAR, never a blocklist of prose words:
death years, status commentary, and wāw co-narrators drop by construction, so
no death-year/commentary/punctuation list is maintained. The lookup tables that
remain are closed linguistic classes for the leading-strip and the rejection
screen, not reactive per-example lists. Precision is load-bearing: a title is
only a title when it LEADS (``أبو الشيخ`` keeps ``الشيخ`` as a kunya tail); a
``فـ``/``وـ`` is only stripped when the remainder is a known compound head
(``فعبد`` → ``عبد`` but ``فضل``/``وهب`` are left whole). CENTRAL-002 keeps the
one regex here compiled through ``patterns``.
"""

from __future__ import annotations

from typing import Final

from backend.build.mizan_names import BIO_MARKERS, decompose
from backend.patterns import cached_compile, normalize_arabic


def _norm_set(words: tuple[str, ...]) -> frozenset[str]:
    """Normalise a tuple of words into a fold-comparable frozenset."""
    return frozenset(normalize_arabic(w) for w in words)


LINKS: Final[frozenset[str]] = _norm_set(("بن", "ابن", "بنت", "ابنة"))

_COMPOUND_HEADS: Final[frozenset[str]] = _norm_set(
    ("عبد", "عبيد", "أبو", "ابو", "أبي", "ابي", "أبا", "ابا", "أم", "ام", "ابن")
)

_CONNECTIVE_VERBS: Final[frozenset[str]] = _norm_set(
    (
        "سألت", "وسألت", "فسألت", "سئل", "سمعت", "وسمعت", "فسمعت", "حدثنا", "حدثني",
        "حدثه", "أخبرنا", "أخبرني", "أنبأنا", "نبأنا", "قال", "وقال", "فقال", "قالوا",
        "قلت", "وقلت", "قلنا", "روى", "رواه", "يروي", "ذكر", "وذكر", "ذكره", "رأيت",
        "قرأت", "كتب", "أنشدنا", "أنشدني", "زعم", "يقول", "قوله", "انتهى", "اقتصر",
    )
)


_TITLE_LEADS: Final[frozenset[str]] = _norm_set(
    (
        "الشيخ", "الشيح", "العلامة", "السيد", "الإمام", "الامام", "الحافظ", "القاضي",
        "المولى", "الأستاذ", "الاستاذ", "الحاكم", "الفقيه", "المحدث", "الأمير",
        "الامير", "المولانا", "مولانا", "الحاج", "الشريف", "الحجة", "الثقة", "المفتي",
        "الزاهد", "العابد", "الورع", "الملك", "السلطان", "الوزير", "الخطيب",
    )
)

_BOOK_LEADS: Final[frozenset[str]] = _norm_set(
    (
        "الأمالي", "الامالي", "الفهرست", "كتاب", "باب", "الجزء", "حديث", "مسند",
        "المسند", "فصل", "رجال", "تاريخ", "التاريخ", "طبقات", "الطبقات", "معجم",
        "المعجم", "الموطأ", "الموطا", "الجامع", "السنن", "الصحيح", "المستدرك",
        "الكامل", "الثقات", "الضعفاء", "العلل", "الميزان", "التهذيب", "التقريب",
        "الاستيعاب", "الإصابة", "الاصابة", "المغني", "الروضة", "المقنع", "الرسالة",
        "ديوان", "شرح", "تفسير", "مختصر", "منتخب", "زوائد", "نوادر", "أخبار",
    )
)

_NON_HEAD: Final[frozenset[str]] = _norm_set(
    ("الله", "رسول", "النبي", "نبي", "نبى", "هذا", "هذه", "بهذا", "وبهذا", "بهذه", "ذلك")
)

_HEADING_LEADS: Final[frozenset[str]] = _norm_set(
    (
        "طبقته", "طبقاته", "طبقة", "شخصيته", "ترجمته", "رواياته", "روايته", "وثاقته",
        "أحواله", "احواله", "نسبه", "كنيته", "مشايخه", "تلاميذه", "تلامذته", "شيوخه",
        "وفاته", "مولده", "اسمه", "لقبه", "عصره", "حياته", "سيرته", "مكانته", "منزلته",
        "آثاره",
    )
)

_TX_STEM_RE = cached_compile(r"^(?:و|ف)?(?:حدث|اخبر|انبا)")
_HAS_ARABIC_RE = cached_compile(r"[ء-ي]")

_BIO_LEADS: Final[frozenset[str]] = _norm_set(tuple(BIO_MARKERS))

_MIN_SIGNIFICANT_TOKENS: Final[int] = 2
_DEFINITE_ARTICLE: Final[str] = "ال"
_PARTICLE_PREFIXES: Final[tuple[str, ...]] = ("لل",)
_STRIPPABLE_PREFIXES: Final[tuple[str, ...]] = ("و", "ف")


def _significant(tokens: list[str]) -> list[str]:
    """The name-bearing tokens: everything that is not a genealogical link (بن ...)."""
    return [t for t in tokens if t not in LINKS]


def _strip_leading_connective(tokens: list[str]) -> list[str]:
    """Drop a leading isnad/speech verb (سألت، حدثنا، قال ...), grading verb (وثقه،

    ضعفه ...), or standalone honorific title (الشيخ، السيد ...) so the real name that
    follows survives. ``سألت يحيى بن معين`` keeps ``يحيى بن معين``; ``وثقه النجاشي``
    reduces to ``النجاشي`` and is rejected later; ``الشيخ محمد بن محمد بن النعمان`` keeps
    ``محمد بن محمد بن النعمان``. Only a LEADING word is dropped, so ``أبو الشيخ`` keeps
    ``الشيخ`` as a kunya tail. Grading verbs reuse :data:`BIO_MARKERS`, the bounded set
    :func:`decompose` stops its walk on, rather than a second hand-maintained list.
    """
    while tokens and (
        normalize_arabic(tokens[0]) in _CONNECTIVE_VERBS
        or normalize_arabic(tokens[0]) in _TITLE_LEADS
        or normalize_arabic(tokens[0]) in _BIO_LEADS
    ):
        tokens = tokens[1:]
    return tokens


def _unglue_prefix(token: str) -> str:
    """Peel a connective ``فـ``/``وـ`` off a token when the remainder is a real name head.

    The remainder is a name head when it is a known compound head (``فعبد`` → ``عبد``)
    or a definite noun (``والنضر`` → ``النضر``, the ``و`` is a conjunction on an
    al-name). ``فضل``/``وهب``/``واصل`` are returned whole: their remainder
    (``ضل``/``هب``/``اصل``) is neither a compound head nor definite, so the letter is
    a root consonant, not a glued conjunction.
    """
    for prefix in _STRIPPABLE_PREFIXES:
        if not token.startswith(prefix):
            continue
        rest = token[len(prefix) :]
        if normalize_arabic(rest) in _COMPOUND_HEADS or rest.startswith(_DEFINITE_ARTICLE):
            return rest
    return token


def clean_name(name: str) -> str:
    """Return the person-name core of a raw string, or '' when nothing name-like remains.

    A raw entry head is ``<name> <biography prose>``; the durable boundary is the name
    GRAMMAR, not a blocklist of prose words. This strips a leading prose word that the
    grammar cannot see because it sits where the ism would go (a narration verb ``سألت``
    or a standalone title ``الشيخ``), ungluess a ``فـ``/``وـ`` conjunction on the head,
    then hands the rest to :func:`decompose`, which walks ism + nasab chain + kunya +
    nisba/laqab and STOPS at the first token that opens biography. Everything past that
    (a death year, ``متهم بالكذب``, ``- 6 أبو بشر``, a wāw co-narrator) is dropped by
    construction, so no death-year/commentary/punctuation list has to be maintained.

    Two structural guards precede the grammar: a token carries a name only when it holds
    an Arabic letter, so entry numbers and separator dashes (``بن -``, ``... بن 506``) are
    dropped rather than parsed as a nasab element; and a leading grading verb the ism slot
    would otherwise swallow (``وثقه النجاشي``) is peeled using :data:`BIO_MARKERS`, the same
    bounded set :func:`decompose` already stops the walk on.
    """
    surface = _strip_leading_connective(
        [token for token in name.strip().split() if _HAS_ARABIC_RE.search(token)]
    )
    if not surface:
        return ""
    surface[0] = _unglue_prefix(surface[0])
    return decompose(" ".join(surface))["name"]


def _leads_with_junk(tokens: list[str]) -> bool:
    """True when the head is a book/heading/verb lead or a genitive particle.

    Titles are not checked here: ``clean_name`` already crops a leading title, so a
    surviving head is either a real name or one of these non-name leads.
    """
    head = tokens[0]
    norm_head = normalize_arabic(head)
    if norm_head in _BOOK_LEADS or norm_head in _HEADING_LEADS or norm_head in _CONNECTIVE_VERBS:
        return True
    if norm_head in _NON_HEAD or norm_head == normalize_arabic("بن"):
        return True
    if any(head.startswith(p) for p in _PARTICLE_PREFIXES):
        return True
    return bool(_TX_STEM_RE.match(norm_head))


def is_person_name(name: str) -> bool:
    """A real person name: not a verb/title/book lead, a particle phrase, or too short."""
    stripped = name.strip()
    if not stripped or stripped[0].isdigit() or stripped[0] in "([":
        return False
    cleaned = clean_name(stripped)
    tokens = cleaned.split()
    if not tokens or _leads_with_junk(tokens):
        return False
    if any(token.startswith(p) for token in tokens for p in _PARTICLE_PREFIXES):
        return False
    return len(_significant([normalize_arabic(t) for t in tokens])) >= _MIN_SIGNIFICANT_TOKENS
