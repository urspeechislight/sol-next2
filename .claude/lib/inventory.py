"""Build a compact symbol inventory of ``src/`` for SessionStart context.

The SessionStart hook injects this into the agent's context so every session
starts knowing which public functions and classes already exist — the first
line of defense against DRY violations (reach for an existing symbol before
writing a new one). It pairs with the ``function_duplication`` handler, which
enforces the same rule deterministically at write time.
"""

from __future__ import annotations

import ast
import logging

from .paths import REPO_ROOT, relpath

_log = logging.getLogger("harness.inventory")

# Bound the context cost. If a growing codebase exceeds this we say so in the
# output rather than silently dropping symbols (fail loud, not silent truncation).
_MAX_SYMBOLS = 400

_SKIP_FILES = frozenset({"__init__.py", "conftest.py"})


def _symbol_label(node: ast.stmt) -> str | None:
    """Return ``"class Name"`` / ``"def name"`` for a public top-level decl, else None."""
    if isinstance(node, ast.ClassDef):
        kind = "class"
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        kind = "def"
    else:
        return None
    if node.name.startswith("_"):
        return None
    return f"{kind} {node.name}"


def _public_symbols(tree: ast.Module) -> list[str]:
    """Return labels for every public class / module-level function in a module."""
    out: list[str] = []
    for node in tree.body:
        label = _symbol_label(node)
        if label is not None:
            out.append(label)
    return out


def build_symbol_inventory() -> str:
    """Render the public-symbol inventory of ``src/`` as a compact text block."""
    lines: list[str] = []
    total = 0
    unparseable: list[str] = []
    truncated = False
    for py in sorted(REPO_ROOT.glob("src/**/*.py")):
        if py.name in _SKIP_FILES:
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, OSError, UnicodeDecodeError) as exc:
            _log.warning("inventory: skipped unparseable %s (%s)", relpath(py), exc)
            unparseable.append(relpath(py))
            continue
        symbols = _public_symbols(tree)
        if not symbols:
            continue
        if total + len(symbols) > _MAX_SYMBOLS:
            truncated = True
            break
        total += len(symbols)
        lines.append(f"{relpath(py)}: {', '.join(symbols)}")

    if not lines:
        return "Codebase symbol inventory: no public symbols under src/ yet."

    header = (
        "Codebase symbol inventory (public functions/classes under src/). "
        "Reuse these: import an existing symbol before writing a new one — "
        "duplicates are blocked by function_duplication (DRY-001 name, DRY-003 body)."
    )
    notes: list[str] = []
    if truncated:
        notes.append(f"(hint only, truncated at {_MAX_SYMBOLS} symbols — more exist)")
    if unparseable:
        notes.append(f"(could not parse: {', '.join(unparseable)})")
    return "\n".join([header, "", *lines, *notes])
