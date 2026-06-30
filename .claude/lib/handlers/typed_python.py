"""Require type hints on public Python functions.

Heuristic: any top-level ``def`` (not starting with ``_``) must have a
return-type annotation. We deliberately don't try to enforce param annotations
at this layer — pyright in CI does that more accurately.

Exemptions:
  • ``__init__`` is required (only ``-> None`` makes sense).
  • The implementation function below an ``@overload`` decorator stack is
    typing-convention exempt — overloads carry the public signatures and the
    impl is intentionally untyped.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision

HANDLER = "typed_python"
RULE_ID = "PY-001"
DOC = "docs/quality-standards.md#code-quality"

# Match top-level (column 0) public defs without return type annotation.
_PUBLIC_DEF = re.compile(
    r"^(?:async\s+)?def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:->[^:]+)?:",
    re.MULTILINE,
)
_HAS_RETURN = re.compile(r"\)\s*->[^:]+:")


def _is_overload_impl(lines: list[str], def_line_idx: int) -> bool:
    """True if any decorator above this def in the same stack is @overload.

    Walks backwards through decorator lines (`@...`) until a non-decorator,
    non-blank line is hit.
    """
    for i in range(def_line_idx - 1, -1, -1):
        stripped = lines[i].strip()
        if not stripped:
            continue
        if stripped.startswith("@"):
            decorator_root = stripped.lstrip("@").split("(", 1)[0].split(".")[-1]
            if decorator_root == "overload":
                return True
            continue
        # Hit a non-decorator non-blank line — the decorator stack ends here.
        return False
    return False


def _previous_def_was_overload(lines: list[str], def_line_idx: int) -> bool:
    """True if a same-named ``@overload``-decorated def appears earlier.

    Catches the second/third overload in a stack where the impl follows
    several `@overload def f(...): ...` declarations.
    """
    name_match = re.match(r"^\s*(?:async\s+)?def\s+(\w+)", lines[def_line_idx])
    if not name_match:
        return False
    name = name_match.group(1)
    pat = re.compile(rf"^\s*def\s+{re.escape(name)}\s*\(")
    for i in range(def_line_idx - 1, -1, -1):
        if pat.match(lines[i]):
            return _is_overload_impl(lines, i) or _previous_def_was_overload(lines, i)
    return False


def check(ctx: HookContext) -> Decision:
    """Return a deny if any public Python function lacks a return-type annotation."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)

    lines = ctx.new_content.splitlines()
    offenders: list[str] = []
    for idx, line in enumerate(lines):
        stripped_async = line.removeprefix("async ")
        if not stripped_async.startswith("def "):
            continue
        match = _PUBLIC_DEF.match(line)
        if not match:
            continue
        name = match.group(1)
        if name.startswith("_") and name != "__init__":
            continue
        if _HAS_RETURN.search(line):
            continue
        # `@overload` chain — the impl below is by convention untyped.
        if _is_overload_impl(lines, idx) or _previous_def_was_overload(lines, idx):
            continue
        offenders.append(name)

    if not offenders:
        return Decision.allow(HANDLER)

    sample = ", ".join(offenders[:3])
    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why=f"Public function(s) without return type: {sample}",
        fix="Add `-> ReturnType:` to each public def. Use `-> None` for procedures.",
        doc=DOC,
    )
