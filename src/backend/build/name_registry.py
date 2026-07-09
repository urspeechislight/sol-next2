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
exposes three operations over them:

  ``clean_name``     strip a leading connective/verb, a glued ``فـ``/``وـ``, crop
                     at the first stop token, drop a trailing relative pronoun.
  ``is_person_name`` after cleaning, reject a title/book/verb lead, a particle
                     phrase (``للـ``), or a too-short remainder.
  ``split_persons``  split a wāw-joined list of people (``البخاري ومسلم وأبي داود``)
                     into individual names.

Precision is load-bearing: a title is only a title when it LEADS (``أبو الشيخ``
keeps ``الشيخ`` as a kunya tail); a ``فـ``/``وـ`` is only stripped when the
remainder is a known compound head (``فعبد`` → ``عبد`` but ``فضل``/``وهب`` are
left whole); wāw only splits before a kunya particle or a corroborated name.
CENTRAL-002 keeps the one regex here compiled through ``patterns``.
"""

from __future__ import annotations

from typing import Final

from backend.patterns import cached_compile, normalize_arabic


def _norm_set(words: tuple[str, ...]) -> frozenset[str]:
    """Normalise a tuple of words into a fold-comparable frozenset."""
    return frozenset(normalize_arabic(w) for w in words)


LINKS: Final[frozenset[str]] = _norm_set(("بن", "ابن", "بنت", "ابنة"))

_COMPOUND_HEADS: Final[frozenset[str]] = _norm_set(
    ("عبد", "عبيد", "أبو", "ابو", "أبي", "ابي", "أبا", "ابا", "أم", "ام", "ابن")
)

_KUNYA_LEADS: Final[frozenset[str]] = _norm_set(
    ("أبو", "ابو", "أبي", "ابي", "أبا", "ابا", "أم", "ام")
)

_CONNECTIVE_VERBS: Final[frozenset[str]] = _norm_set(
    (
        "سألت", "وسألت", "فسألت", "سئل", "سمعت", "وسمعت", "فسمعت", "حدثنا", "حدثني",
        "حدثه", "أخبرنا", "أخبرني", "أنبأنا", "نبأنا", "قال", "وقال", "فقال", "قالوا",
        "قلت", "وقلت", "قلنا", "روى", "رواه", "يروي", "ذكر", "وذكر", "ذكره", "رأيت",
        "قرأت", "كتب", "أنشدنا", "أنشدني", "زعم", "يقول", "قوله", "انتهى", "اقتصر",
        "اتهمه", "اتهم", "متهم", "مذكور", "كذبه", "ضعفه", "وثقه", "رماه", "رموه",
        "غمزه", "تركه", "وهاه", "نسبوه", "قيل", "وقيل", "ويقال", "يقال",
    )
)

_STOP_TOKENS: Final[frozenset[str]] = _norm_set(
    (
        "عن", "من", "في", "بين", "إلى", "الى", "مع", "ثم", "الذي", "التي", "الذين",
        "مولى", "مولاه", "منسوب", "أخبار", "الجمع", "بهذا", "بهذه", "الاسناد",
        "الإسناد", "قال", "يقول", "سمعت", "أنه", "أنها", "لما", "وكان", "كان",
        "يعرف", "المعروف", "يكنى", "لقبه", "الملقب", "غير", "لم", "به", "منه",
        "عمن", "عنه", "عنهم", "مرفوعا", "موقوفا", "مسندا", "معلقا", "سنة", "مات", "توفي",
    )
)

_TRAILING_DROP: Final[frozenset[str]] = _norm_set(("الذي", "التي", "الذين", "غيره", "وغيره"))
_HAS_ARABIC_RE = cached_compile(r"[ء-ي]")

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

_NON_HEAD: Final[frozenset[str]] = _norm_set(("الله", "رسول", "النبي", "نبي", "نبى"))

_HEADING_LEADS: Final[frozenset[str]] = _norm_set(
    (
        "طبقته", "طبقاته", "طبقة", "شخصيته", "ترجمته", "رواياته", "روايته", "وثاقته",
        "أحواله", "احواله", "نسبه", "كنيته", "مشايخه", "تلاميذه", "تلامذته", "شيوخه",
        "وفاته", "مولده", "اسمه", "لقبه", "عصره", "حياته", "سيرته", "مكانته", "منزلته",
        "آثاره",
    )
)

_TX_STEM_RE = cached_compile(r"^(?:و|ف)?(?:حدث|اخبر|انبا)")

_MIN_SIGNIFICANT_TOKENS: Final[int] = 2
_DEFINITE_ARTICLE: Final[str] = "ال"
_PARTICLE_PREFIXES: Final[tuple[str, ...]] = ("لل",)
_STRIPPABLE_PREFIXES: Final[tuple[str, ...]] = ("و", "ف")


def _significant(tokens: list[str]) -> list[str]:
    """The name-bearing tokens: everything that is not a genealogical link (بن ...)."""
    return [t for t in tokens if t not in LINKS]


def _strip_leading_connective(tokens: list[str]) -> list[str]:
    """Drop a leading isnad/speech verb (سألت، حدثنا، قال ...) or standalone honorific

    title (الشيخ، السيد ...) so the real name that follows survives. ``سألت يحيى بن
    معين`` keeps ``يحيى بن معين``; ``الشيخ محمد بن محمد بن النعمان`` keeps ``محمد بن
    محمد بن النعمان``; a bare ``سألت أبي`` reduces to ``أبي`` and is rejected later.
    Only a LEADING title is dropped, so ``أبو الشيخ`` keeps ``الشيخ`` as a kunya tail.
    """
    while tokens and (
        normalize_arabic(tokens[0]) in _CONNECTIVE_VERBS
        or normalize_arabic(tokens[0]) in _TITLE_LEADS
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

    Strips a leading connective verb, ungluess a ``فـ``/``وـ`` on the head, crops at
    the first stop token (``عن``/``ثم``/``مولى``/``اتهمه`` ...), and drops a trailing
    relative pronoun, a bare death-year number (``… الأشعري 191``), or an honorific
    sign - any trailing token with no Arabic letter. The surface tokens are otherwise
    preserved (only trimmed), so char offsets into a kept slice stay valid.
    """
    surface = name.strip().split()
    while surface and not _HAS_ARABIC_RE.search(surface[0]):
        surface = surface[1:]
    if not surface:
        return ""
    surface = _strip_leading_connective(surface)
    if not surface:
        return ""
    surface[0] = _unglue_prefix(surface[0])
    norm = [normalize_arabic(t) for t in surface]
    cut = len(surface)
    for i in range(1, len(surface)):
        token = surface[i]
        if (
            norm[i] in _STOP_TOKENS
            or norm[i] in _CONNECTIVE_VERBS
            or not _HAS_ARABIC_RE.search(token)
            or len(token) == 1
        ):
            cut = i
            break
    surface = surface[:cut]
    while surface and (
        normalize_arabic(surface[-1]) in _TRAILING_DROP or not _HAS_ARABIC_RE.search(surface[-1])
    ):
        surface = surface[:-1]
    return " ".join(surface)


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


def is_name(name: str) -> bool:
    """A looser name-shape check for a teacher/student edge label (not a chain lead).

    Edge names are already single tokens-of-a-list; this only rejects an obvious
    connective/verb lead and requires two significant tokens, without the full
    title/book/particle screening ``is_person_name`` applies to a corpus record.
    """
    tokens = [normalize_arabic(t) for t in name.split()]
    if not tokens or tokens[0] in _CONNECTIVE_VERBS or _TX_STEM_RE.match(tokens[0]):
        return False
    return len(_significant(tokens)) >= _MIN_SIGNIFICANT_TOKENS


def _is_join_boundary(token: str) -> bool:
    """True when a wāw-prefixed token opens a new person in a joined list.

    High-confidence only: ``وأبي``/``وأبو``/``وأم`` (a wāw glued to a kunya particle)
    or ``وابن``. This splits ``... وأبي داود`` off cleanly while leaving names whose
    own first letter is wāw (``وهب``, ``وكيع``) untouched, since their remainder is
    not a kunya particle.
    """
    if not token.startswith("و"):
        return False
    rest = normalize_arabic(token[1:])
    return rest in _KUNYA_LEADS or rest == normalize_arabic("ابن")


def split_persons(name: str) -> list[str]:
    """Split a wāw-joined list of people into individual cleaned names.

    Only splits at a high-confidence boundary (a wāw glued to a kunya particle),
    so ``البخاري ومسلم وأبي داود`` yields the run up to each ``وأبي`` boundary while
    ``عبد الله بن وهب`` stays whole. Each part is cleaned; empties drop out.
    """
    surface = name.strip().split()
    if not surface:
        return []
    parts: list[list[str]] = [[]]
    for token in surface:
        if _is_join_boundary(token) and parts[-1]:
            parts.append([token[1:]])
        else:
            parts.append(parts.pop() + [token])
    cleaned = [clean_name(" ".join(part)) for part in parts]
    return [c for c in cleaned if c]
