"""Co-narrator name-splitting helpers for the hadith extractor.

split_co_narrators splits a name slice containing co-narrators joined by
conjunction (، و or bare و) into individual name parts; snap_name_end_to_word_
boundary extends a cut position to the next word boundary so a name truncated
mid-word is captured whole. Split out of hadith.py to keep that module under the
size cap. Ported from sol-next's src/extractors/hadith_names.py; the helpers are
public (no underscore) because hadith.py imports them across modules.
"""

from __future__ import annotations

from backend.patterns import CompiledPattern, cached_compile

_COMMA_WAW_SPLIT_REGEX: CompiledPattern = cached_compile(r"،\s*و")
_BARE_WAW_REGEX: CompiledPattern = cached_compile(r"\s+و")
_IBN_BEFORE_WAW_REGEX: CompiledPattern = cached_compile(r"(?:بن|ابن)\s*$")
_WORD_BOUNDARY_CHARS: frozenset[str] = frozenset(" \t\n\r،,:.؟?؛")


def split_co_narrators(name_slice: str, relative_references: list[str]) -> list[str]:
    """Split a name slice containing co-narrators joined by conjunction.

    Comma-waw (، و) always splits — unambiguous Arabic co-narrator syntax. Bare
    waw (و) splits with guards: not when preceded by بن/ابن (بن وهب is a name),
    not when followed by a relative reference (وأبيه) or an identity
    clarification (هو/هي). Returns [name_slice] when no split applies.
    """
    parts = _COMMA_WAW_SPLIT_REGEX.split(name_slice)
    if len(parts) > 1:
        return [part.strip() for part in parts if part.strip()]

    result: list[str] = []
    remaining = name_slice
    while remaining:
        match = _BARE_WAW_REGEX.search(remaining)
        if match is None:
            result.append(remaining)
            break
        before = remaining[: match.start()]
        after = remaining[match.end() :]
        if not _bare_waw_splits(before, after, relative_references):
            result.append(remaining)
            break
        if before.strip():
            result.append(before)
        remaining = after
    return [part.strip() for part in result if part.strip()] or [name_slice]


def _bare_waw_splits(before: str, after: str, relative_references: list[str]) -> bool:
    """Return True when a bare و at this position is a co-narrator conjunction.

    Guards against splitting a name-internal و: the و is not a conjunction when it
    follows بن/ابن (بن وهب), opens a relative reference (وأبيه), or opens an
    identity clarification (وهو/هي).
    """
    if _IBN_BEFORE_WAW_REGEX.search(before):
        return False
    after_stripped = after.lstrip()
    if any(after_stripped.startswith(ref) for ref in relative_references):
        return False
    return not after_stripped.startswith(("هو", "هي"))


def snap_name_end_to_word_boundary(text: str, pos: int) -> int:
    """Extend pos to the end of the current word when it falls mid-word.

    When isnad_end lands mid-name (truncating عقيل to ع), extend to the next
    whitespace/punctuation boundary so the full name is captured. When pos is
    already at a boundary (preceded by such a char) or at/past the text end, it is
    returned unchanged.
    """
    if pos <= 0 or pos >= len(text):
        return pos
    if text[pos - 1] in _WORD_BOUNDARY_CHARS:
        return pos
    while pos < len(text) and text[pos] not in _WORD_BOUNDARY_CHARS:
        pos += 1
    return pos
