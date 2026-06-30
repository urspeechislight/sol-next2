"""Block silent-fallback patterns in error paths — fail fast, fail loud.

Pairs with ``no_silent_except`` (which blocks the literal ``except: pass``
patterns) by catching the *subtler* shape of the same bug: an except body
that returns a default value or substitutes a fallback **without logging**.

The patterns blocked here, all inside an ``except`` handler:

  1. ``return None`` / ``return []`` / ``return {}`` / ``return ()``
     when no logging call appears earlier in the same handler body.
  2. ``return "UNKNOWN"`` / ``return "unknown"`` / ``return "N/A"`` —
     placeholder strings that lie to the caller about success.
  3. ``continue`` as the only meaningful statement.

Why: a function that swallows the exception and returns ``None`` looks
identical to a function that returned ``None`` because of normal data. The
caller cannot tell the difference, and the bug never surfaces. The user's
rule: "wrong is worse than absent" — either log and re-raise, or log and
return an explicit ``Result`` / ``Failure`` value.

Heuristic for "did the handler log before falling back?": we walk the
expression statements that precede the offending return/continue and look
for any call whose attribute chain contains ``log``, ``logger``,
``warning``, ``error``, ``critical``, ``debug``, ``info``, or whose name
matches ``raise``. If anything matched, the handler is loud; we allow.
"""

from __future__ import annotations

import ast

from ..context import HookContext
from ..decision import Decision

HANDLER = "fail_loud"
RULE_ID = "FAILFAST-001"
DOC = "docs/quality-standards.md#fail-fast"

_PLACEHOLDER_STRINGS: frozenset[str] = frozenset(
    {"UNKNOWN", "unknown", "N/A", "n/a", "default", "DEFAULT", ""}
)


def _is_empty_collection(node: ast.expr) -> bool:
    """True if `node` is `[]`, `{}`, `()` (empty collection literal)."""
    if isinstance(node, ast.List) and not node.elts:
        return True
    if isinstance(node, ast.Dict) and not node.keys:
        return True
    if isinstance(node, ast.Tuple) and not node.elts:
        return True
    if isinstance(node, ast.Set) and not node.elts:
        return True
    return False


def _is_silent_value(node: ast.expr | None) -> bool:
    """True if `node` is a silent-fallback value (None, empty coll, placeholder str)."""
    if node is None:
        return True
    if isinstance(node, ast.Constant):
        if node.value is None:
            return True
        if isinstance(node.value, str) and node.value in _PLACEHOLDER_STRINGS:
            return True
    return _is_empty_collection(node)


def _names_in_call(call: ast.Call) -> str:
    """Return a dotted name like 'self.logger.error' or 'log' from a Call."""
    parts: list[str] = []
    node: ast.expr = call.func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


_LOUD_NEEDLES: tuple[str, ...] = (
    "log",
    "logger",
    "warning",
    "error",
    "critical",
    "debug",
    "info",
    "exception",
)


def _is_loud(stmts: list[ast.stmt]) -> bool:
    """True if any statement up to this point logs the exception or raises."""
    for s in stmts:
        if isinstance(s, ast.Raise):
            return True
        for node in ast.walk(s):
            if isinstance(node, ast.Call):
                name = _names_in_call(node)
                if any(needle in name.lower() for needle in _LOUD_NEEDLES):
                    return True
    return False


def _find_silent_falls(handler: ast.ExceptHandler) -> ast.stmt | None:
    """Return the first silent-fallback statement in `handler`, or None."""
    body = handler.body
    for i, stmt in enumerate(body):
        preceding = body[:i]
        if isinstance(stmt, ast.Return) and _is_silent_value(stmt.value):
            if not _is_loud(preceding):
                return stmt
        if isinstance(stmt, ast.Continue) and not _is_loud(preceding):
            return stmt
        if isinstance(stmt, ast.Pass) and not _is_loud(preceding) and len(body) == 1:
            return stmt
    return None


def check(ctx: HookContext) -> Decision:
    """Block silent-fallback shapes inside Python except handlers."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    try:
        tree = ast.parse(ctx.new_content)
    except SyntaxError:
        return Decision.allow(HANDLER)

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            offender = _find_silent_falls(node)
            if offender is None:
                continue
            shape = _describe(offender)
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    f"Silent fallback in `except` block (line {offender.lineno}): {shape}. "
                    "No log call, no raise, no advisory before the fallback."
                ),
                fix=(
                    "Either log the exception (e.g. "
                    "`logger.error('parse failed', exc_info=True)`) before returning, "
                    "or re-raise (`raise NewError(...) from e`). The caller must be able "
                    "to tell a failure from a legitimate empty result."
                ),
                doc=DOC,
            )
    return Decision.allow(HANDLER)


def _describe(stmt: ast.stmt) -> str:
    """Human-readable summary of the offending statement."""
    if isinstance(stmt, ast.Return):
        if stmt.value is None or (isinstance(stmt.value, ast.Constant) and stmt.value.value is None):
            return "`return None`"
        if isinstance(stmt.value, ast.List):
            return "`return []`"
        if isinstance(stmt.value, ast.Dict):
            return "`return {}`"
        if isinstance(stmt.value, ast.Tuple):
            return "`return ()`"
        if isinstance(stmt.value, ast.Constant):
            return f"`return {stmt.value.value!r}`"
        return "`return <silent-default>`"
    if isinstance(stmt, ast.Continue):
        return "`continue`"
    if isinstance(stmt, ast.Pass):
        return "`pass`"
    return "silent fallback"
