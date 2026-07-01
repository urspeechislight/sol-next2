"""Enforce single-responsibility constraints on function definitions.

Four checks, each a signal that a function is doing too much:

  1. **Vague name**: ``helper``, ``process``, ``handle``, ``do_stuff`` say
     *that* a function helps, not *what* it does.
  2. **Multi-responsibility name**: ``_and_`` / ``_then_`` / ``_or_`` in a name
     means it bundles independent steps that should be separate functions.
  3. **Over-long name**: a name longer than 40 chars usually encodes a
     responsibility list.
  4. **Too many parameters**: more than 5 parameters (excluding ``self`` /
     ``cls``) means the call site juggles too much.

Checks 1-3 are naming invariants and block (FUNC-001). Check 4 is advisory
(FUNC-002): when the param count was a hard block it manufactured transfer
dataclasses whose only job was to smuggle the same arguments past the gate,
which is strictly worse than a wide signature. A wide signature is a design
smell the author must weigh, so it warns instead. When a file trips both, the
blocking naming violation is reported and the advisory is dropped.

Scope: ``.py`` files, skipping tests and ``__init__.py``.
"""

from __future__ import annotations

import ast

from ..context import HookContext
from ..decision import Decision

HANDLER = "helper_constraints"
RULE_ID = "FUNC-001"
RULE_ID_PARAMS = "FUNC-002"
DOC = "docs/quality-standards.md#helper-functions"

MAX_PARAMS = 5
MAX_NAME_LEN = 40
_VAGUE: frozenset[str] = frozenset(
    {
        "helper", "do_stuff", "do_things", "process", "handle", "execute", "run",
        "perform", "util", "utils", "misc", "common", "general", "wrapper",
        "inner", "temp", "tmp", "foo", "bar", "baz", "func", "function",
    }
)
_MULTI_MARKERS = ("_and_", "_then_", "_or_")
_FuncDef = (ast.FunctionDef, ast.AsyncFunctionDef)


def _param_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count named parameters, excluding ``self`` / ``cls``."""
    args = node.args
    named = args.posonlyargs + args.args + args.kwonlyargs
    return sum(1 for a in named if a.arg not in {"self", "cls"})


def _name_violation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, str] | None:
    """Return `(why, fix)` for the first naming invariant `node` breaks, else None."""
    name = node.name
    base = name.lstrip("_")
    if base in _VAGUE:
        return (
            f"Function `{name}` (line {node.lineno}) has a vague name.",
            "Rename it to describe what it does, e.g. `parse_isnad`, not `process`.",
        )
    if any(marker in name for marker in _MULTI_MARKERS):
        return (
            f"Function `{name}` (line {node.lineno}) bundles multiple responsibilities.",
            "Split into one function per step, e.g. `parse_input` + `validate_input`.",
        )
    if len(name) > MAX_NAME_LEN:
        return (
            f"Function name `{name}` (line {node.lineno}) exceeds {MAX_NAME_LEN} chars.",
            "A shorter name usually means a tighter responsibility; split or rename.",
        )
    return None


def _param_violation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, str] | None:
    """Return `(why, fix)` if `node` exceeds the parameter signal, else None."""
    count = _param_count(node)
    if count > MAX_PARAMS:
        return (
            f"Function `{node.name}` (line {node.lineno}) takes {count} params "
            f"(signal is {MAX_PARAMS}).",
            (
                "Consider whether a cohesive domain object should own some of "
                "these. Do not invent a transfer dataclass just to shrink the "
                "signature; a wide explicit signature beats a fake bundle."
            ),
        )
    return None


def check(ctx: HookContext) -> Decision:
    """Block naming-invariant breaks; advise on wide parameter lists."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    if ctx.file_path is not None:
        name = ctx.file_path.name
        if name == "__init__.py" or name.startswith("test_") or name.endswith("_test.py"):
            return Decision.allow(HANDLER)

    try:
        tree = ast.parse(ctx.new_content)
    except SyntaxError:
        return Decision.allow(HANDLER)

    param_result: tuple[str, str] | None = None
    for node in ast.walk(tree):
        if not isinstance(node, _FuncDef):
            continue
        name_result = _name_violation(node)
        if name_result is not None:
            why, fix = name_result
            return Decision.deny(handler=HANDLER, rule_id=RULE_ID, why=why, fix=fix, doc=DOC)
        if param_result is None:
            param_result = _param_violation(node)
    if param_result is not None:
        why, fix = param_result
        return Decision.advise(handler=HANDLER, rule_id=RULE_ID_PARAMS, why=why, fix=fix, doc=DOC)
    return Decision.allow(HANDLER)
