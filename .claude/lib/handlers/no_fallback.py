"""Hard-block fallback patterns. Fallbacks hide real failures.

This is the strict sibling of ``fail_loud``. ``fail_loud`` permits
"log + return None" if a log call ran first. ``no_fallback`` rejects
*any* error-recovery that lets the program continue without telling the
caller something failed. The user's rule: "wrong is worse than absent."

What gets blocked
-----------------

1. The word ``fallback`` / ``fall back`` / ``fall-back`` (case-insensitive)
   appearing anywhere in source content — comments, strings, identifiers.
   The word almost always names the banned pattern; if the pattern needs
   to be described, do it in ``.claude/`` or ``docs/`` (out of scope), or
   rephrase ("prefer X; otherwise Y", "default to Y", "use Y when X is
   absent"). No escape valve — the ban is the point.

2. Python ``except`` handlers whose body does not contain a ``raise``
   statement. Loud logging is good but not enough; the exception must
   propagate (or be converted via ``raise NewError(...) from e``).

3. JavaScript / TypeScript ``catch`` blocks whose body does not contain
   a ``throw`` statement. Same reasoning as Python.

Scope
-----

Applies under ``src/**/*.{py,js,jsx,ts,tsx}`` and ``scripts/**/*.py``.
``.claude/``, ``tests/``, ``docs/`` are exempt — the harness itself,
its tests, and project documentation must be able to NAME the banned
pattern when blocking, testing, or explaining it.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from ..context import HookContext
from ..decision import Decision
from ..paths import REPO_ROOT

HANDLER = "no_fallback"
RULE_ID = "FAILFAST-002"
DOC = "docs/quality-standards.md#fail-fast"

_IN_SCOPE_PREFIXES: tuple[str, ...] = ("src/", "scripts/")
_OUT_OF_SCOPE_PREFIXES: tuple[str, ...] = (".claude/", "tests/", "docs/")
_LANG_SUFFIXES: frozenset[str] = frozenset({"py", "js", "jsx", "ts", "tsx"})
_PY_SUFFIXES: frozenset[str] = frozenset({"py"})
_JS_SUFFIXES: frozenset[str] = frozenset({"js", "jsx", "ts", "tsx"})

# Matches "fallback", "Fallback", "fall-back", "fall back", and the
# inflected forms "fallbacks", "falls back", "falling back". Whole-word
# anchored so "rollback" / "snowfall" / "feedback" don't trip it.
_WORD_PATTERN = re.compile(r"\bfall(?:ing|s)?[ \-]?back(?:s)?\b", re.IGNORECASE)

# JS catch block opener: `catch (e)` or `catch` (optional binding).
_JS_CATCH_OPENER = re.compile(r"\bcatch\s*(?:\([^)]*\))?\s*\{")

# Promise.catch(<silent arrow>) — `.catch(() => null)`, `.catch(e => '')`.
# Restricted to the unambiguous "silent value" shape — the RHS may not
# contain `(`, `{`, or `)` so we don't false-positive on block-form arrows
# (which usually carry a real `throw`) or on function-call expressions
# (which might throw via the callee). Aggressive form is over-detection
# territory and best left to PR review.
_PROMISE_CATCH_ARROW = re.compile(
    r"\.catch\s*\(\s*(?:\(\s*\w*\s*\)|\w+)\s*=>\s*([^(){}]*?)\s*\)",
)

_FIX = (
    "Fallbacks hide real failures. Replace with `raise`/`throw` so the "
    "error propagates and the caller decides how to handle it. If absence "
    "is a legitimate result, model it explicitly in the producer "
    "(`Optional[T]`, `T | None` returned directly without a try/except). "
    "Rule of thumb: 'wrong is worse than absent.'"
)


def _repo_relative(path: Path | None) -> str | None:
    """Return the repo-relative path, or None if path is outside REPO_ROOT."""
    if path is None:
        return None
    resolved = path.resolve()
    if not resolved.is_relative_to(REPO_ROOT):
        return None
    return resolved.relative_to(REPO_ROOT).as_posix()


def _in_scope(rel: str) -> bool:
    """True if this path is subject to the rule."""
    if any(rel.startswith(p) for p in _OUT_OF_SCOPE_PREFIXES):
        return False
    return any(rel.startswith(p) for p in _IN_SCOPE_PREFIXES)


def _find_word(content: str) -> tuple[int, str] | None:
    """Return (line, snippet) of the first banned-word hit, or None."""
    m = _WORD_PATTERN.search(content)
    if not m:
        return None
    # Locate the line number.
    line_no = content.count("\n", 0, m.start()) + 1
    # Snippet — the line itself, trimmed.
    line_start = content.rfind("\n", 0, m.start()) + 1
    line_end = content.find("\n", m.end())
    snippet = content[line_start : line_end if line_end != -1 else len(content)].strip()
    if len(snippet) > 120:
        snippet = snippet[:117] + "..."
    return line_no, snippet


def _python_except_without_raise(content: str) -> ast.ExceptHandler | None:
    """Return the first except handler whose body lacks a raise, or None."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if not _body_contains_raise(node.body):
                return node
    return None


def _body_contains_raise(body: list[ast.stmt]) -> bool:
    """True if any statement (or nested statement) in body is a Raise."""
    for stmt in body:
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Raise):
                return True
    return False


def _find_js_catch_without_throw(content: str) -> tuple[int, str] | None:
    """Return (line, body-snippet) of the first JS catch missing throw, or None.

    Checks two shapes:
      1. ``catch (e) { ... }`` block-form — brace-matched scan honoring
         nesting and string literals; body must contain ``throw``.
      2. ``.catch(e => RHS)`` Promise method — RHS must contain ``throw``
         or ``Promise.reject``.

    Does NOT use a JS parser (would require adding babel/acorn as a
    harness dep). Covers the obvious shapes; subtle cases (named
    callbacks like ``.catch(handleError)``) are left to PR review.
    """
    # Shape 1: try/catch block-form.
    pos = 0
    while True:
        opener = _JS_CATCH_OPENER.search(content, pos)
        if not opener:
            break
        brace_open = opener.end() - 1
        body_end = _match_brace(content, brace_open)
        if body_end is None:
            break
        body = content[brace_open + 1 : body_end]
        if not _js_body_contains_throw(body):
            line_no = content.count("\n", 0, opener.start()) + 1
            snippet = body.strip().replace("\n", " ")
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            return line_no, f"catch {{ {snippet} }}"
        pos = body_end + 1

    # Shape 2: Promise.catch(arrow) form.
    for m in _PROMISE_CATCH_ARROW.finditer(content):
        rhs = m.group(1)
        if _js_body_contains_throw(rhs) or "Promise.reject" in rhs:
            continue
        line_no = content.count("\n", 0, m.start()) + 1
        snippet = m.group(0).replace("\n", " ")
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        return line_no, snippet

    return None


def _match_brace(content: str, open_idx: int) -> int | None:
    """Return the index of the closing brace matching content[open_idx]='{'."""
    depth = 1
    i = open_idx + 1
    in_string: str | None = None
    while i < len(content):
        c = content[i]
        if in_string is not None:
            if c == "\\":
                i += 2
                continue
            if c == in_string:
                in_string = None
        elif c in {'"', "'", "`"}:
            in_string = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _js_body_contains_throw(body: str) -> bool:
    """True if `body` contains a throw statement (cheap text scan)."""
    # `throw ` or `throw\n` — exclude `throws` (TypeScript JSDoc).
    return bool(re.search(r"\bthrow\b(?!s)", body))


def check(ctx: HookContext) -> Decision:
    """Hard-block fallback patterns in src/ and scripts/."""
    if not ctx.is_write or ctx.new_content is None or ctx.file_path is None:
        return Decision.allow(HANDLER)
    if ctx.suffix not in _LANG_SUFFIXES:
        return Decision.allow(HANDLER)
    rel = _repo_relative(ctx.file_path)
    if rel is None or not _in_scope(rel):
        return Decision.allow(HANDLER)

    word = _find_word(ctx.new_content)
    if word is not None:
        line, snippet = word
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why=(
                f"`fallback` (or `fall back` / `fall-back`) found at line {line}: "
                f"{snippet!r}. The word names a banned pattern; using it suggests "
                "the code (or its rationale) describes a silent error-recovery path."
            ),
            fix=_FIX,
            doc=DOC,
        )

    if ctx.suffix in _PY_SUFFIXES:
        handler = _python_except_without_raise(ctx.new_content)
        if handler is not None:
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    f"`except` block at line {handler.lineno} does not `raise`. "
                    "Loud logging is good but not enough — the exception must "
                    "propagate (or convert to a typed error via "
                    "`raise NewError(...) from e`)."
                ),
                fix=_FIX,
                doc=DOC,
            )
    elif ctx.suffix in _JS_SUFFIXES:
        offender = _find_js_catch_without_throw(ctx.new_content)
        if offender is not None:
            line, snippet = offender
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    f"`catch` block at line {line} does not `throw`. "
                    f"Body: {snippet!r}. Every caught error must re-throw "
                    "(possibly as a typed error) — silently swallowing it "
                    "hides real failures."
                ),
                fix=_FIX,
                doc=DOC,
            )

    return Decision.allow(HANDLER)
