"""Require a docstring on every public function and class.

Why: public functions and classes are the API surface other code reads. A
docstring as the first statement documents intent at the point of use. This
enforces the documentation bar on the public API surface.

Scope: ``.py`` files, skipping tests and ``__init__.py``. A symbol is public
when its name does not start with ``_``. ``@overload`` stubs are exempt — the
overload set documents the signatures and the implementation carries the
docstring.
"""

from __future__ import annotations

import ast

from ..context import HookContext
from ..decision import Decision

HANDLER = "docstring_required"
RULE_ID = "DOC-010"
DOC = "docs/quality-standards.md#docstrings"

_Def = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _is_overload(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if the function is decorated with ``@overload``."""
    for dec in node.decorator_list:
        root = dec.id if isinstance(dec, ast.Name) else getattr(dec, "attr", "")
        if root == "overload":
            return True
    return False


def check(ctx: HookContext) -> Decision:
    """Block public defs/classes that lack a docstring as their first statement."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    if ctx.file_path is None:
        return Decision.allow(HANDLER)
    name = ctx.file_path.name
    if name == "__init__.py" or name.startswith("test_") or name.endswith("_test.py"):
        return Decision.allow(HANDLER)
    if name == "conftest.py":
        return Decision.allow(HANDLER)

    try:
        tree = ast.parse(ctx.new_content)
    except SyntaxError:
        return Decision.allow(HANDLER)

    for node in ast.walk(tree):
        if not isinstance(node, _Def):
            continue
        if node.name.startswith("_"):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_overload(node):
            continue
        if ast.get_docstring(node) is None:
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=f"Public {kind} `{node.name}` (line {node.lineno}) has no docstring.",
                fix=(
                    "Add a docstring as the first statement. Describe what the "
                    f"{kind} does and its contract — one line is enough for simple cases."
                ),
                doc=DOC,
            )
    return Decision.allow(HANDLER)
