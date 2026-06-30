"""Block module-level class-name collisions across files in ``src/``.

Why: classes are the carriers of *schemas* — DTOs (Pydantic ``BaseModel``,
``dataclass``), enums (``Enum``, ``IntEnum``), typed dicts, named tuples,
and exception classes. Two ``Book`` models in two files diverge silently;
two ``ValidationError`` exceptions trip up handlers that catch the wrong
one; two ``UserRole`` enums let callers pass values the other side can't
parse. This is the same SSOT bug as duplicated functions, just at the
type level.

What this handler does on every Write/Edit to a ``.py`` file under ``src/``:

  1. Parse the new content. Collect names of **module-level**, public
     class definitions.
  2. Index every other ``.py`` file under ``src/`` for the same shape.
  3. Block when a class with the same name is already defined elsewhere.

Exempt:

  * Private classes (``_Foo``) — they're file-private.
  * ``conftest.py`` — pytest fixture classes intentionally repeat.
  * Classes named after framework patterns where one-per-module is the
    convention: ``Config``, ``Meta`` (Pydantic / SQLAlchemy / Django
    inner-config sentinels).
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

from ..context import HookContext
from ..decision import Decision
from ..paths import REPO_ROOT, is_in, relpath

HANDLER = "class_duplication"
RULE_ID = "DRY-002"
DOC = "docs/quality-standards.md#ssot-dry"

_PRODUCTION = ("src",)
_EXEMPT_NAMES: frozenset[str] = frozenset({"Config", "Meta"})


def _is_exempt_name(name: str) -> bool:
    """True if `name` is conventionally allowed to appear once per module."""
    if name.startswith("_"):
        return True
    return name in _EXEMPT_NAMES


def _public_module_classes(tree: ast.Module) -> list[str]:
    """Return names of module-level public class definitions."""
    out: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not _is_exempt_name(node.name):
            out.append(node.name)
    return out


def _iter_repo_py(exclude: Path | None) -> Iterable[Path]:
    """Yield production .py files under src/, skipping file under edit + conftests."""
    for py in REPO_ROOT.glob("src/**/*.py"):
        if exclude is not None and py.resolve() == exclude:
            continue
        if py.name == "conftest.py":
            continue
        yield py


def _index_existing(exclude: Path | None) -> dict[str, Path]:
    """Return ``{class_name: defining_file}`` for src/**/*.py."""
    index: dict[str, Path] = {}
    for py in _iter_repo_py(exclude):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue
        for name in _public_module_classes(tree):
            index.setdefault(name, py)
    return index


def check(ctx: HookContext) -> Decision:
    """Block when a public class name collides across files in src/."""
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

    new_classes = _public_module_classes(tree)
    if not new_classes:
        return Decision.allow(HANDLER)

    index = _index_existing(ctx.file_path)
    for name in new_classes:
        if name in index:
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    f"Class `{name}` is already defined in `{relpath(index[name])}`. "
                    "Two definitions of the same type drift silently — pick one home."
                ),
                fix=(
                    f"Import the existing `{name}` from `{_module_path(index[name])}` "
                    "and delete this copy. If the behaviours are genuinely different, "
                    "rename this one (e.g. `BookSummary` vs `BookDetail`)."
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
