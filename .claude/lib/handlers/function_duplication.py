"""Block duplicate functions across files in ``src/``.

Two DRY violations are caught on every Write/Edit to a ``.py`` file under
``src/`` (the handler reads the rest of the tree itself — the HookContext only
carries the new content):

  * **DRY-001 — name collision.** A public module-level ``def`` / ``async def``
    whose name already exists in another src file. The classic "two
    ``normalize_arabic``" drift.
  * **DRY-003 — body collision under a different name.** A function whose body
    is structurally identical (same AST, ignoring the function name and a
    leading docstring) to one already defined elsewhere — i.e.
    copy-paste-and-rename. Only bodies with at least ``_MIN_BODY_STATEMENTS``
    statements are considered, so trivial one-liners (``return None``) never
    false-positive. (DRY-002 belongs to ``class_duplication``.)

Exempt names that are conventionally one-per-module:

  * ``main`` — CLI entry points.
  * ``create_app`` / ``get_app`` — framework factory pattern.
  * Anything starting with ``_`` (file-private) or ``test_`` (pytest names).

Pytest fixtures collide across conftest files by design; conftest.py is skipped.
"""

from __future__ import annotations

import ast
import hashlib
import logging
from collections.abc import Iterable
from pathlib import Path

from ..context import HookContext
from ..decision import Decision
from ..paths import REPO_ROOT, is_in, relpath

HANDLER = "function_duplication"
RULE_ID = "DRY-001"
RULE_ID_BODY = "DRY-003"
DOC = "docs/quality-standards.md#ssot-dry"

_log = logging.getLogger("harness.function_duplication")

_PRODUCTION = ("src",)
_EXEMPT_NAMES: frozenset[str] = frozenset({"main", "create_app", "get_app"})
# Bodies shorter than this are too trivial for an identical-body match to mean
# "copy-paste duplicate" — many distinct functions share a 1-2 statement shape.
_MIN_BODY_STATEMENTS = 3

_FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


def _is_exempt_name(name: str) -> bool:
    """True if `name` is conventionally allowed to appear once per module."""
    if name.startswith("_"):
        return True
    if name.startswith("test_"):
        return True
    return name in _EXEMPT_NAMES


def _public_function_nodes(tree: ast.Module) -> list[_FunctionNode]:
    """Return module-level public ``def`` / ``async def`` nodes (non-exempt)."""
    out: list[_FunctionNode] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not _is_exempt_name(
            node.name
        ):
            out.append(node)
    return out


def _body_fingerprint(node: _FunctionNode) -> str | None:
    """SHA-256 of a function body AST, ignoring its name and a leading docstring.

    Returns ``None`` when the body has fewer than ``_MIN_BODY_STATEMENTS``
    statements — too trivial for an identical match to imply duplication.
    """
    body = list(node.body)
    first = body[0] if body else None
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        body = body[1:]
    if len(body) < _MIN_BODY_STATEMENTS:
        return None
    dumped = "\n".join(ast.dump(stmt) for stmt in body)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def _iter_repo_py(exclude: Path | None) -> Iterable[Path]:
    """Yield production .py files under src/, skipping the file under edit
    and conftest files (whose duplicate fixture names are intentional).
    """
    for py in REPO_ROOT.glob("src/**/*.py"):
        if exclude is not None and py.resolve() == exclude:
            continue
        if py.name == "conftest.py":
            continue
        yield py


def _index_existing(exclude: Path | None) -> tuple[dict[str, Path], dict[str, tuple[str, Path]]]:
    """Return ``(by_name, by_body)`` indexes for src/**/*.py.

    ``by_name`` maps ``function_name -> file``; ``by_body`` maps
    ``body_fingerprint -> (function_name, file)``.
    """
    by_name: dict[str, Path] = {}
    by_body: dict[str, tuple[str, Path]] = {}
    for py in _iter_repo_py(exclude):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, OSError, UnicodeDecodeError) as exc:
            _log.warning("function_duplication: skipped %s (%s)", relpath(py), exc)
            continue
        for node in _public_function_nodes(tree):
            by_name.setdefault(node.name, py)
            fingerprint = _body_fingerprint(node)
            if fingerprint is not None:
                by_body.setdefault(fingerprint, (node.name, py))
    return by_name, by_body


def _name_collision(node: _FunctionNode, by_name: dict[str, Path]) -> Decision | None:
    """Deny if `node`'s name already lives in another src file (DRY-001)."""
    if node.name not in by_name:
        return None
    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why=(
            f"Public function `{node.name}` is already defined in "
            f"`{relpath(by_name[node.name])}`. Two definitions is DRY violation."
        ),
        fix=(
            f"Either import the existing `{node.name}` from "
            f"`{_module_path(by_name[node.name])}` and delete this copy, or "
            f"rename this one so the behaviours are explicitly different "
            "(e.g. `parse_arabic_strict` vs `parse_arabic_lenient`)."
        ),
        doc=DOC,
    )


def _body_collision(node: _FunctionNode, by_body: dict[str, tuple[str, Path]]) -> Decision | None:
    """Deny if `node`'s body matches an existing function under a different name (DRY-003)."""
    fingerprint = _body_fingerprint(node)
    if fingerprint is None or fingerprint not in by_body:
        return None
    existing_name, existing_file = by_body[fingerprint]
    if existing_name == node.name:
        return None
    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID_BODY,
        why=(
            f"Function `{node.name}` has the same body as `{existing_name}` in "
            f"`{relpath(existing_file)}` — a copy-paste duplicate under a different name."
        ),
        fix=(
            "Extract the shared logic into one function and import it in both "
            "places, or — if they must stay separate — change the implementation "
            "so the two are genuinely different."
        ),
        doc=DOC,
    )


def check(ctx: HookContext) -> Decision:
    """Block name (DRY-001) and body (DRY-003) duplicates across files in src/."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    if not is_in(ctx.file_path, *_PRODUCTION):
        return Decision.allow(HANDLER)
    if ctx.file_path is not None and ctx.file_path.name == "conftest.py":
        return Decision.allow(HANDLER)

    try:
        tree = ast.parse(ctx.new_content)
    except SyntaxError:
        return Decision.allow(HANDLER)

    new_nodes = _public_function_nodes(tree)
    if not new_nodes:
        return Decision.allow(HANDLER)

    by_name, by_body = _index_existing(ctx.file_path)
    for node in new_nodes:
        decision = _name_collision(node, by_name) or _body_collision(node, by_body)
        if decision is not None:
            return decision
    return Decision.allow(HANDLER)


def _module_path(file: Path) -> str:
    """Render a path like `src/backend/foo/bar.py` as `src.backend.foo.bar`."""
    try:
        rel = file.resolve().relative_to(REPO_ROOT).with_suffix("")
    except ValueError:
        return file.stem
    return ".".join(rel.parts)
