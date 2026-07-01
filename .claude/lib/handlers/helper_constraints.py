"""Enforce single-responsibility constraints on function definitions.

Four checks, each a signal that a function is doing too much:

  1. **Vague name** — ``helper``, ``process``, ``handle``, ``do_stuff`` … say
     *that* a function helps, not *what* it does.
  2. **Multi-responsibility name** — ``_and_`` / ``_then_`` / ``_or_`` in a name
     means it bundles independent steps that should be separate functions.
  3. **Over-long name** — a name longer than 40 chars usually encodes a
     responsibility list.
  4. **Too many parameters** — more than 5 parameters (excluding ``self`` /
     ``cls``) means the call site juggles too much; group them into a
     dataclass / params object.

Scope: ``.py`` files, skipping tests and ``__init__.py``.
"""

from __future__ import annotations

import ast

from ..context import HookContext
from ..decision import Decision

HANDLER = "helper_constraints"
RULE_ID = "FUNC-001"
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


def _violation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, str] | None:
    """Return `(why, fix)` for the first constraint `node` breaks, else None."""
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
            "A shorter name usually means a tighter responsibility — split or rename.",
        )
    count = _param_count(node)
    if count > MAX_PARAMS:
        return (
            f"Function `{name}` (line {node.lineno}) takes {count} params (max {MAX_PARAMS}).",
            "Group related parameters into a dataclass / params object, or split the function.",
        )
    return None


def check(ctx: HookContext) -> Decision:
    """Block functions that break a single-responsibility constraint."""
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

    for node in ast.walk(tree):
        if not isinstance(node, _FuncDef):
            continue
        result = _violation(node)
        if result is not None:
            why, fix = result
            return Decision.deny(handler=HANDLER, rule_id=RULE_ID, why=why, fix=fix, doc=DOC)
    return Decision.allow(HANDLER)
