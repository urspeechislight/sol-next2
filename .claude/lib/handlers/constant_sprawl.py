"""Block constant sprawl — enforce SSOT for module-level constants.

Why: when two files each define their own ``TIMEOUT_SECONDS = 30``, the
codebase has two sources of truth. Changing the value in one place silently
breaks the other. The user's rule: "if a constant doesn't exist is the only
time you can create one."

What this handler does on every Write/Edit to a ``.py`` file under ``src/``:

  1. Parse the new content. Collect module-level ``UPPER_CASE = <literal>``
     assignments — both ``Assign`` and ``AnnAssign`` forms.
  2. Index every other ``.py`` file under ``src/`` for the same shape.
  3. Block if:
        a. NAME collision — a constant with the same UPPER_CASE name is
           already defined in a different file. Pick one home and import.
        b. VALUE collision — a constant with a *different* name has the
           *same* literal value. Reuse the existing one instead of minting
           a new alias.

Allowed values that intentionally repeat (and so are excluded from
value-collision checks): ``-1, 0, 1, 2, 100`` and the empty literals
``""``, ``[]``, ``{}``, ``()``, ``None``, ``True``, ``False``.

The handler reads files from disk on every invocation. For sol-next2's
size (low hundreds of .py files), this is sub-100ms. If the index needs to
become persistent we can move to a SQLite shelf — but premature.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

from ..context import HookContext
from ..decision import Decision
from ..paths import REPO_ROOT, is_in, relpath

HANDLER = "constant_sprawl"
RULE_ID = "SSOT-001"
DOC = "docs/quality-standards.md#ssot-dry"

_PRODUCTION = ("src",)

# Values so universal that two constants legitimately share them. Adding a
# value here is the only knob this handler exposes; keep it short.
_TRIVIAL_INT_FLOAT: frozenset[int | float] = frozenset({-1, 0, 1, 2, 100, 200})
_TRIVIAL_STR: frozenset[str] = frozenset({"", "/", "."})


def _literal(node: ast.expr) -> object | None:
    """Return a Python value for literal AST nodes; None for non-literals."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple) and all(isinstance(e, ast.Constant) for e in node.elts):
        return tuple(e.value for e in node.elts if isinstance(e, ast.Constant))
    if isinstance(node, ast.List) and all(isinstance(e, ast.Constant) for e in node.elts):
        return tuple(e.value for e in node.elts if isinstance(e, ast.Constant))  # list -> tuple, hashable
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _literal(node.operand)
        if isinstance(inner, (int, float)):
            return -inner
    return None


def _is_trivial(value: object) -> bool:
    """True if this value is so common that name collisions on it aren't sprawl."""
    if isinstance(value, bool) or value is None:
        return True
    if isinstance(value, (int, float)) and value in _TRIVIAL_INT_FLOAT:
        return True
    if isinstance(value, str) and value in _TRIVIAL_STR:
        return True
    if isinstance(value, tuple) and not value:
        return True
    return False


def _module_constants(tree: ast.Module) -> list[tuple[str, object]]:
    """Return (name, value) pairs for module-level UPPER_CASE = literal."""
    out: list[tuple[str, object]] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _is_const_name(target.id):
                    value = _literal(node.value)
                    if value is not None or isinstance(node.value, ast.Constant):
                        out.append((target.id, value))
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            tgt = node.target
            if isinstance(tgt, ast.Name) and _is_const_name(tgt.id):
                value = _literal(node.value)
                if value is not None or isinstance(node.value, ast.Constant):
                    out.append((tgt.id, value))
    return out


def _is_const_name(name: str) -> bool:
    """True if `name` looks like a module-level constant (UPPER_SNAKE_CASE)."""
    if not name or name.startswith("_"):
        return False
    return name.isupper() or name.replace("_", "").isupper()


def _iter_repo_py(exclude: Path | None) -> Iterable[Path]:
    """Yield production .py files under src/, skipping the file under edit."""
    for py in REPO_ROOT.glob("src/**/*.py"):
        if exclude is not None and py.resolve() == exclude:
            continue
        yield py


def _index_existing(exclude: Path | None) -> tuple[dict[str, Path], dict[object, list[tuple[str, Path]]]]:
    """Return (by_name, by_value) indexes of existing module-level constants."""
    by_name: dict[str, Path] = {}
    by_value: dict[object, list[tuple[str, Path]]] = {}
    for py in _iter_repo_py(exclude):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue
        for name, value in _module_constants(tree):
            by_name.setdefault(name, py)
            if value is not None and not _is_trivial(value):
                try:
                    by_value.setdefault(value, []).append((name, py))
                except TypeError:
                    continue  # unhashable — skip
    return by_name, by_value


def check(ctx: HookContext) -> Decision:
    """Block name- or value-collisions for new module-level constants."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    if not is_in(ctx.file_path, *_PRODUCTION):
        return Decision.allow(HANDLER)

    try:
        tree = ast.parse(ctx.new_content)
    except SyntaxError:
        return Decision.allow(HANDLER)

    new_constants = _module_constants(tree)
    if not new_constants:
        return Decision.allow(HANDLER)

    by_name, by_value = _index_existing(ctx.file_path)

    for name, value in new_constants:
        if name in by_name:
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    f"Constant `{name}` is already defined in `{relpath(by_name[name])}`. "
                    "Two definitions of the same name is sprawl — pick one home and import."
                ),
                fix=(
                    f"Delete this assignment and `from {_module_path(by_name[name])} import "
                    f"{name}` instead. If the values are genuinely different concepts, "
                    "rename this one so the difference is visible."
                ),
                doc=DOC,
            )
        if value is None or _is_trivial(value):
            continue
        try:
            collisions = by_value.get(value, [])
        except TypeError:
            collisions = []
        if collisions:
            existing_name, existing_file = collisions[0]
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    f"Constant `{name} = {value!r}` duplicates the value of "
                    f"`{existing_name}` in `{relpath(existing_file)}`. "
                    "Reuse the existing constant — do not mint an alias."
                ),
                fix=(
                    f"Delete `{name}` and use the existing `{existing_name}` "
                    f"(import from `{_module_path(existing_file)}`). Create a new "
                    "constant only when no existing one fits semantically."
                ),
                doc=DOC,
            )
    return Decision.allow(HANDLER)


def _module_path(file: Path) -> str:
    """Render a path like `src/backend/foo/bar.py` as `src.backend.foo.bar`."""
    try:
        rel = file.resolve().relative_to(REPO_ROOT).with_suffix("")
    except ValueError:
        return file.stem
    return ".".join(rel.parts)
