"""Transliterate Arabic narrator names to a Latin (ALA-LC-style) reading.

Unvocalized Arabic carries no short vowels, so a character map alone yields
consonant skeletons (ʿbd for ʿAbd). A token map supplies the correctly vowelled
reading of the common name components - the kunya particles, the frequent isms,
and the frequent nisbas that make up the bulk of narrator names; the character
map covers the rare remaining tokens. The result is approximate by nature and
meant as a reading aid above the authoritative Arabic.
"""

from __future__ import annotations

from typing import Final

from backend.core.constants import ARABIC__DEFINITE_ARTICLE as _AL

_CHAR: Final[dict[str, str]] = {
    "ا": "a", "أ": "a", "إ": "i", "آ": "ā", "ب": "b", "ت": "t", "ث": "th",
    "ج": "j", "ح": "ḥ", "خ": "kh", "د": "d", "ذ": "dh", "ر": "r", "ز": "z",
    "س": "s", "ش": "sh", "ص": "ṣ", "ض": "ḍ", "ط": "ṭ", "ظ": "ẓ", "ع": "ʿ",
    "غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "و": "ū", "ي": "ī", "ى": "ā", "ة": "a", "ء": "ʾ", "ئ": "ʾ", "ؤ": "ʾ",
}

_TOKEN: Final[dict[str, str]] = {
    "أبو": "Abū", "أبا": "Abā", "أبي": "Abī", "ابو": "Abū", "ابي": "Abī", "ابا": "Abā",
    "ابن": "Ibn", "بن": "b.", "بنت": "bint", "أم": "Umm", "ام": "Umm",
    "عبد": "ʿAbd", "الله": "Allāh", "عبيد": "ʿUbayd", "أبيه": "Abīhi", "مولى": "mawlā",
    "محمد": "Muḥammad", "أحمد": "Aḥmad", "علي": "ʿAlī", "عمر": "ʿUmar", "عمرو": "ʿAmr",
    "عثمان": "ʿUthmān", "الحسن": "al-Ḥasan", "الحسين": "al-Ḥusayn", "حسن": "Ḥasan",
    "حسين": "Ḥusayn", "جعفر": "Jaʿfar", "يزيد": "Yazīd", "جابر": "Jābir", "زياد": "Ziyād",
    "سفيان": "Sufyān", "مالك": "Mālik", "أنس": "Anas", "زيد": "Zayd", "عيينة": "ʿUyayna",
    "خالد": "Khālid", "سعيد": "Saʿīd", "سعد": "Saʿd", "إبراهيم": "Ibrāhīm", "اسحاق": "Isḥāq",
    "إسماعيل": "Ismāʿīl", "يحيى": "Yaḥyā", "يعقوب": "Yaʿqūb", "يوسف": "Yūsuf", "إسحاق": "Isḥāq",
    "موسى": "Mūsā", "عيسى": "ʿĪsā", "هارون": "Hārūn", "سليمان": "Sulaymān", "طاوس": "Ṭāwūs",
    "داود": "Dāwūd", "الرحمن": "al-Raḥmān", "بكر": "Bakr", "طلحة": "Ṭalḥa", "معاوية": "Muʿāwiya",
    "عطاء": "ʿAṭāʾ", "شعبة": "Shuʿba", "قتادة": "Qatāda", "الأعمش": "al-Aʿmash", "حماد": "Ḥammād",
    "نافع": "Nāfiʿ", "مجاهد": "Mujāhid", "عكرمة": "ʿIkrima", "الزهري": "al-Zuhrī", "هشام": "Hishām",
    "بشير": "Bashīr", "النعمان": "al-Nuʿmān", "المفضل": "al-Mufaḍḍal", "الصفار": "al-Ṣaffār",
    "النضر": "al-Naḍr", "القاسم": "al-Qāsim", "الوليد": "al-Walīd", "الحارث": "al-Ḥārith",
    "المنذر": "al-Mundhir", "صالح": "Ṣāliḥ", "منصور": "Manṣūr", "معمر": "Maʿmar", "وكيع": "Wakīʿ",
    "عائشة": "ʿĀʾisha", "فاطمة": "Fāṭima", "أبان": "Abān", "أيوب": "Ayyūb", "بلال": "Bilāl",
    "الجعفي": "al-Jaʿfī", "القمي": "al-Qummī", "الكوفي": "al-Kūfī", "المدني": "al-Madanī",
    "المكي": "al-Makkī", "البصري": "al-Baṣrī", "البغدادي": "al-Baghdādī", "الدمشقي": "al-Dimashqī",
    "المصري": "al-Miṣrī", "الشامي": "al-Shāmī", "اليماني": "al-Yamānī", "الرازي": "al-Rāzī",
    "الهمداني": "al-Hamdānī", "الخراساني": "al-Khurāsānī", "الواسطي": "al-Wāsiṭī", "الأصبهاني": "al-Aṣbahānī",
    "النيسابوري": "al-Naysābūrī", "الحمصي": "al-Ḥimṣī", "الأنصاري": "al-Anṣārī", "الهلالي": "al-Hilālī",
    "التميمي": "al-Tamīmī", "الأسدي": "al-Asadī", "المخزومي": "al-Makhzūmī", "العجلي": "al-ʿIjlī",
    "السلمي": "al-Sulamī", "الثقفي": "al-Thaqafī", "الجمحي": "al-Jumaḥī", "الأشعري": "al-Ashʿarī",
}


def _char_translit(token: str) -> str:
    """Transliterate one unknown token character by character, honouring an al- prefix."""
    prefix = ""
    body = token
    if body.startswith(_AL) and len(body) > len(_AL):
        prefix = "al-"
        body = body[len(_AL):]
    letters = "".join(_CHAR.get(char, "") for char in body)
    letters = letters.capitalize() if not prefix else letters
    return prefix + letters


def transliterate(name: str) -> str:
    """Transliterate an Arabic name token by token; unknown tokens use the char map."""
    out: list[str] = []
    for token in name.split():
        if token in _TOKEN:
            out.append(_TOKEN[token])
        elif token.startswith(_AL) and token[len(_AL):] in _TOKEN:
            mapped = _TOKEN[token[len(_AL):]]
            out.append(mapped if mapped.startswith("al-") else "al-" + mapped)
        else:
            out.append(_char_translit(token))
    return " ".join(part for part in out if part)
