"""Advise on functions over 80 LOC. Advisory only, never a block.

Python is scanned via indent-tracking (``_PY_DEF`` matches ``def`` and
``async def``; the scanner counts contiguous indented body lines). TS/JS is
scanned via brace matching over three function-shaped openers (declaration,
arrow assignment, class method), each capturing the function name. The
parsers are deliberately simple, not full ASTs; good enough to catch
egregious cases, and deeper analysis happens in CI.

Why advisory rather than blocking: a hard cap forces mechanical extraction
at an arbitrary line count, which produces param-bag dataclasses and
half-concept helpers instead of real design improvements. A long function
is a redesign signal the author must weigh; the advisory keeps the signal
without forcing the wrong fix.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision

HANDLER = "function_size_cap"
LIMIT = 80
DOC = "docs/quality-standards.md#size-caps"

_PY_DEF = re.compile(r"^(\s*)(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)

_TS_FN_DECL = re.compile(r"\b(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*[<(]")
_TS_FN_ARROW = re.compile(r"\b(?:export\s+)?(?:const|let|var)\s+(\w+)\s*[:=][^=\n]*=>\s*\{?")
_TS_METHOD = re.compile(
    r"^\s+(?:async\s+|public\s+|private\s+|protected\s+|static\s+)*(\w+)\s*\([^)]*\)\s*[:{]",
    re.MULTILINE,
)


def _scan_python(content: str) -> list[tuple[str, int]]:
    """Return `(name, loc)` for each Python function exceeding LIMIT."""
    out: list[tuple[str, int]] = []
    lines = content.splitlines()
    for match in _PY_DEF.finditer(content):
        start_line_idx = content[: match.start()].count("\n")
        indent = len(match.group(1))
        name = match.group(2)
        body_loc = 0
        for i in range(start_line_idx + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                continue
            line_indent = len(line) - len(line.lstrip())
            if line_indent <= indent:
                break
            body_loc += 1
        if body_loc > LIMIT:
            out.append((name, body_loc))
    return out


def _count_braces_body(content: str, opening_brace_pos: int) -> int:  # noqa: PLR0912  -- brace-state machine has unavoidable branches
    """Starting at the position of an opening `{`, return the LOC of the
    body until the matching closing brace.

    Tracks brace depth. Skips chars inside strings (single/double/backtick)
    and ``//``-style line comments and ``/* */`` block comments. A template
    literal ``${...}`` expression is treated as opaque text up to the next
    backtick. Returns -1 if the body is unterminated.
    """
    if opening_brace_pos >= len(content) or content[opening_brace_pos] != "{":
        return 0
    depth = 0
    i = opening_brace_pos
    n = len(content)
    start_line = content.count("\n", 0, i)
    while i < n:
        ch = content[i]
        if ch == "/" and i + 1 < n and content[i + 1] == "/":
            nl = content.find("\n", i)
            if nl == -1:
                break
            i = nl + 1
            continue
        if ch == "/" and i + 1 < n and content[i + 1] == "*":
            end = content.find("*/", i + 2)
            if end == -1:
                return -1
            i = end + 2
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            j = i + 1
            while j < n:
                if content[j] == "\\":
                    j += 2
                    continue
                if content[j] == quote:
                    break
                j += 1
            i = j + 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end_line = content.count("\n", 0, i)
                return end_line - start_line
        i += 1
    return -1


def _scan_ts(content: str) -> list[tuple[str, int]]:
    """Return `(name, loc)` for each TS/JS function exceeding LIMIT.

    The ``seen`` set of opening-brace positions avoids double-reporting a
    function whose signature matches more than one opener pattern. For each
    match the scanner finds the next ``{`` after the signature and measures
    the body from there.
    """
    out: list[tuple[str, int]] = []
    seen: set[int] = set()
    for pattern in (_TS_FN_DECL, _TS_FN_ARROW, _TS_METHOD):
        for match in pattern.finditer(content):
            start = match.end()
            brace = content.find("{", start)
            if brace == -1 or brace in seen:
                continue
            seen.add(brace)
            loc = _count_braces_body(content, brace)
            if loc > LIMIT:
                out.append((match.group(1), loc))
    return out


def check(ctx: HookContext) -> Decision:
    """Advise when any function exceeds LIMIT LOC; never block."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)
    if ctx.suffix == "py":
        offenders = _scan_python(ctx.new_content)
    elif ctx.suffix in {"ts", "tsx", "js", "jsx"}:
        offenders = _scan_ts(ctx.new_content)
    else:
        return Decision.allow(HANDLER)

    if offenders:
        name, loc = offenders[0]
        return Decision.advise(
            handler=HANDLER,
            rule_id="QUAL-011",
            why=f"Function `{name}` is {loc} LOC; the redesign signal is {LIMIT}.",
            fix=(
                "Extract a named operation that stands on its own. Do not carve "
                "at an arbitrary line or invent a params object just to move "
                "lines; a long cohesive function beats a false decomposition."
            ),
            doc=DOC,
        )
    return Decision.allow(HANDLER)
