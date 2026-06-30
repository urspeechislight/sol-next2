"""Block magic numeric literals in production Python code.

Why: a literal like ``42`` or ``3600`` buried in code is a comprehension
hazard — the reader doesn't know what it represents. Named constants
explain intent and make values reusable.

Allowed literals (per CLAUDE.md): ``-1, 0, 1, 2, 100``. Anything else in
``src/`` triggers a **block** (upgraded from advisory at the user's
request — strict SSOT/DRY). Tests, scripts, and ``constants.py`` are exempt.
"""

from __future__ import annotations

import ast

from ..context import HookContext
from ..decision import Decision
from ..paths import is_in

HANDLER = "magic_numbers"
RULE_ID = "QUAL-014"
DOC = "docs/quality-standards.md#code-quality"

_ALLOWED: frozenset[int | float] = frozenset({-1, 0, 1, 2, 100})
_PRODUCTION = ("src",)


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.bad: list[tuple[int, int | float]] = []
        self._in_annotation = 0

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        # Constants in annotations (Literal[200]) are fine.
        self._in_annotation += 1
        self.generic_visit(node)
        self._in_annotation -= 1

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # Anything inside a subscript like Literal[200] / Annotated[..., 200] — exempt.
        self._in_annotation += 1
        self.generic_visit(node)
        self._in_annotation -= 1

    def visit_Constant(self, node: ast.Constant) -> None:
        if self._in_annotation:
            return
        v = node.value
        if isinstance(v, bool):  # bool is subclass of int — skip
            return
        if isinstance(v, (int, float)) and v not in _ALLOWED:
            self.bad.append((node.lineno, v))


def check(ctx: HookContext) -> Decision:
    """Advisory if magic numbers appear in production Python code."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    if not is_in(ctx.file_path, *_PRODUCTION):
        return Decision.allow(HANDLER)
    # Allow definition file for constants — that's what we WANT magic values in.
    if ctx.file_path is not None and ctx.file_path.name == "constants.py":
        return Decision.allow(HANDLER)

    try:
        tree = ast.parse(ctx.new_content)
    except SyntaxError:
        return Decision.allow(HANDLER)

    visitor = _Visitor()
    visitor.visit(tree)
    if not visitor.bad:
        return Decision.allow(HANDLER)

    sample = ", ".join(f"{v} (line {ln})" for ln, v in visitor.bad[:3])
    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why=f"Magic numeric literal(s) in production code: {sample}.",
        fix=(
            "Move to a named constant in `core/constants.py` (or service equivalent). "
            "Before creating a new constant, check `constant_sprawl` rules — reuse "
            "an existing constant if one with the same value already exists. "
            "Allowed bare literals: -1, 0, 1, 2, 100."
        ),
        doc=DOC,
    )
