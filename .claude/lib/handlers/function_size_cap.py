"""Block functions over 80 LOC. Python via indent-tracking; TS/JS via brace
matching.

Uses deliberately simple parsers — not full ASTs. Good enough to catch
egregious violations; deeper analysis happens in CI.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision

HANDLER = "function_size_cap"
LIMIT = 80
DOC = "docs/quality-standards.md#size-caps"

# Python: def or async def, indented body. Counts contiguous indented lines.
_PY_DEF = re.compile(r"^(\s*)(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)

# TS/JS function-shape openers we care about. Each captures the function name.
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
    and ``//``-style line comments and ``/* */`` block comments. Returns -1
    if the body is unterminated.
    """
    if opening_brace_pos >= len(content) or content[opening_brace_pos] != "{":
        return 0
    depth = 0
    i = opening_brace_pos
    n = len(content)
    start_line = content.count("\n", 0, i)
    while i < n:
        ch = content[i]
        # Line comment
        if ch == "/" and i + 1 < n and content[i + 1] == "/":
            nl = content.find("\n", i)
            if nl == -1:
                break
            i = nl + 1
            continue
        # Block comment
        if ch == "/" and i + 1 < n and content[i + 1] == "*":
            end = content.find("*/", i + 2)
            if end == -1:
                return -1
            i = end + 2
            continue
        # String
        if ch in ("'", '"', "`"):
            quote = ch
            j = i + 1
            while j < n:
                if content[j] == "\\":
                    j += 2
                    continue
                if content[j] == quote:
                    break
                # Template literal expression — track braces, but for
                # simplicity treat ${...} as opaque text up to next backtick.
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
    """Return `(name, loc)` for each TS/JS function exceeding LIMIT."""
    out: list[tuple[str, int]] = []
    seen: set[int] = set()  # avoid double-reporting overlapping matches
    for pattern in (_TS_FN_DECL, _TS_FN_ARROW, _TS_METHOD):
        for match in pattern.finditer(content):
            start = match.end()
            # Find the next `{` after the signature.
            brace = content.find("{", start)
            if brace == -1 or brace in seen:
                continue
            seen.add(brace)
            loc = _count_braces_body(content, brace)
            if loc > LIMIT:
                out.append((match.group(1), loc))
    return out


def check(ctx: HookContext) -> Decision:
    """Return deny if any function exceeds LIMIT LOC."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)
    if ctx.suffix == "py":
        offenders = _scan_python(ctx.new_content)
    elif ctx.suffix in {"ts", "tsx", "js", "jsx", "svelte"}:
        offenders = _scan_ts(ctx.new_content)
    else:
        return Decision.allow(HANDLER)

    if offenders:
        name, loc = offenders[0]
        return Decision.deny(
            handler=HANDLER,
            rule_id="QUAL-011",
            why=f"Function `{name}` is {loc} LOC; cap is {LIMIT}.",
            fix="Extract helpers; favor small, named operations over long bodies.",
            doc=DOC,
        )
    return Decision.allow(HANDLER)
