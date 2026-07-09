"""Hard-block self-admitted patchwork in application source.

The sibling of ``no_fallback``. Where ``no_fallback`` bans the word that
names a silent error-recovery path, this bans the vocabulary a developer
reaches for when they KNOW a change is a corner-cut rather than a durable
fix: ``band-aid``, ``stopgap``, ``kludge``, ``quick fix``, ``patchwork``,
and the like. Like ``fallback``, these words have no legitimate reason to
appear in shipped application code: their only use is to confess that the
code papers over a symptom instead of resolving the root cause. The ban is
the point, since if the word fits, the code needs a proper fix, not the word.

This is the mechanical floor of a layered defence, not the whole of it. It
catches the honest confession. The semantic pattern the user actually hit,
a reactive blocklist grown one bad example at a time with no confession in
the text, is caught by the push-time AI review (``scripts/cca_review.sh``)
and the session durability directive in ``CLAUDE.md``. A regex cannot judge
whether an enumeration is a closed linguistic class or a growing patch pile;
a reader can.

What gets blocked
-----------------

The closed confession vocabulary in ``_PATCHWORK_PATTERN`` covers band-aid,
stopgap, kludge, duct-tape, patchwork, patch-job, quick-fix, quick-and-dirty,
hacky, "good enough for now", matched whole-word and case-insensitive as a
comment, string, or identifier anywhere in application source. Compound
admissions allow an optional space or hyphen between halves so the spelling
variants (band aid / band-aid / bandaid) collapse to one alternative. The list
is a closed class of corner-cut admissions, not an open-ended keyword pile; it
grows only if a genuinely new admission idiom appears, the same footing as the
``fallback`` ban.

Scope
-----

Application source across the whole project: ``src/**`` (backend and pipeline
Python) and ``frontend/src/**`` (the React app), for ``.{py,js,jsx,ts,tsx}``
files. ``scripts/`` is exempt so build and review tooling (``cca_review.sh``
names the pattern it hunts) can talk about patchwork; ``.claude/``, ``tests/``,
and ``docs/`` are exempt so the harness, its tests, and the project's own
documentation can name the banned words when enforcing, testing, or explaining
them.
"""

from __future__ import annotations

import re

from .. import paths
from ..context import HookContext
from ..decision import Decision

HANDLER = "no_patchwork"
RULE_ID = "PATCH-001"
DOC = "docs/quality-standards.md#no-patchwork"

_APP_SOURCE_ROOTS: tuple[str, ...] = ("src", "frontend/src")
_LANG_SUFFIXES: frozenset[str] = frozenset({"py", "js", "jsx", "ts", "tsx"})

_PATCHWORK_PATTERN = re.compile(
    r"\b("
    r"band[ \-]?aid|"
    r"stop[ \-]?gap|"
    r"kludg(?:e|es|y|ey)|cludge|"
    r"duct[ \-]?tape|"
    r"patch[ \-]?work|patch[ \-]?job|"
    r"quick[ \-]?(?:fix|hack)|quick[ \-]?and[ \-]?dirty|"
    r"hacky|"
    r"good enough for now"
    r")\b",
    re.IGNORECASE,
)

_FIX = (
    "This word admits a corner-cut. Resolve the root cause and delete what the "
    "fix replaces, rather than papering over the symptom and naming the paper. "
    "If the change filters or classifies domain data, encode the structural or "
    "grammatical rule that decides membership, never an enumeration of bad "
    "examples grown one bug at a time. If you cannot do it properly now, stop "
    "and surface it rather than shipping the patch and labelling it."
)


def _find_admission(content: str) -> tuple[int, str, str] | None:
    """Return (line, matched-term, line-snippet) of the first hit, or None."""
    match = _PATCHWORK_PATTERN.search(content)
    if match is None:
        return None
    line_no = content.count("\n", 0, match.start()) + 1
    line_start = content.rfind("\n", 0, match.start()) + 1
    line_end = content.find("\n", match.end())
    snippet = content[line_start : line_end if line_end != -1 else len(content)].strip()
    if len(snippet) > 120:
        snippet = snippet[:117] + "..."
    return line_no, match.group(0), snippet


def check(ctx: HookContext) -> Decision:
    """Hard-block self-admitted patchwork vocabulary in application source."""
    if not ctx.is_write or ctx.new_content is None or ctx.file_path is None:
        return Decision.allow(HANDLER)
    if ctx.suffix not in _LANG_SUFFIXES:
        return Decision.allow(HANDLER)
    if not paths.is_in(ctx.file_path, *_APP_SOURCE_ROOTS):
        return Decision.allow(HANDLER)

    admission = _find_admission(ctx.new_content)
    if admission is not None:
        line, term, snippet = admission
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why=(
                f"Patchwork admission {term!r} found at line {line}: {snippet!r}. "
                "The word names a corner-cut; using it in application source signals "
                "the code papers over a symptom instead of resolving the root cause."
            ),
            fix=_FIX,
            doc=DOC,
        )

    return Decision.allow(HANDLER)
