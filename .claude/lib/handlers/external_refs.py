"""Block external project references (the harness must remain standalone).

Why: this repo is a re-implementation of an existing project. If the agent
ever writes a path or import that points at a sibling project under
``~/code/`` (sol-next, sol-app, ...), the standalone contract is broken. The
committed deny-list covers the public sol-* family; any other internal names
load from a gitignored ``external_refs.private`` so they are enforced on this
machine without ever being committed. We catch references at write time:

  - Absolute / tilde paths: ``/home/.../code/sol-next/...`` or ``~/code/sol-app/...``
  - JS/TS imports: ``from 'sol-next/x'``
  - Python imports: ``from sol_next import x`` / ``import sol_app``
  - Path traversal: ``../sol-next/...`` (relative)
"""

from __future__ import annotations

import re
from pathlib import Path

from ..context import HookContext
from ..decision import Decision

HANDLER = "external_refs"
RULE_ID = "ISO-001"
DOC = "docs/foundation.md#standalone-contract"


def load_private_refs(path: Path | None = None) -> tuple[str, ...]:
    """Extra banned project names from a gitignored local file, one per line
    (``#`` comments and blank lines ignored). Keeps internal names out of the
    committed history while still enforcing them on this machine."""
    target = path or (Path(__file__).resolve().parent.parent.parent / "external_refs.private")
    if not target.exists():
        return ()
    return tuple(
        stripped
        for line in target.read_text(encoding="utf-8").splitlines()
        if (stripped := line.strip()) and not stripped.startswith("#")
    )


# Forbidden project names, kebab-case (filesystem) and snake_case (Python
# module) forms both checked. The committed list is the public sol-* family;
# load_private_refs adds any internal names from the gitignored
# external_refs.private so they are enforced locally but never committed.
_FORBIDDEN_KEBAB = (
    "sol-next",
    "sol-app",
    "sol-codex",
) + load_private_refs()


def _kebab_to_snake(name: str) -> str:
    return name.replace("-", "_")


_FORBIDDEN_SNAKE = tuple(_kebab_to_snake(n) for n in _FORBIDDEN_KEBAB)
_FORBIDDEN_ALL = tuple(set(_FORBIDDEN_KEBAB) | set(_FORBIDDEN_SNAKE))

_PATH_PATTERN = re.compile(
    r"(?:/home/[^/\s'\"]+/code|~/code|\.\.[/\\][\w./\\-]*)/(?P<n>"
    + "|".join(re.escape(n) for n in _FORBIDDEN_ALL)
    + r")\b"
)
# JS/TS imports / require() / dynamic import.
_JS_IMPORT = re.compile(r"""(?:from|import|require)\s*\(?\s*['"]([^'"]+)['"]""")
# Python imports — bare module names.
_PY_IMPORT = re.compile(
    r"^\s*(?:from\s+(?P<from>[\w.]+)|import\s+(?P<import>[\w., ]+))",
    re.MULTILINE,
)


def _js_path_is_external(import_path: str) -> bool:
    """True if a JS/TS import path points to a sibling project."""
    lowered = import_path.lower()
    if lowered.startswith(("/", "~", "..", "/home/")):
        return any(name in lowered for name in _FORBIDDEN_ALL)
    first_segment = lowered.split("/", 1)[0].split(".", 1)[0]
    return first_segment in _FORBIDDEN_ALL


def _py_module_is_external(module: str) -> bool:
    """True if a Python module name's root is a forbidden project."""
    root = module.strip().split(".", 1)[0]
    return root in _FORBIDDEN_ALL


def check(ctx: HookContext) -> Decision:  # noqa: PLR0911  -- one return per deny pattern
    """Return a deny if external project references appear."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)
    # Markdown deliberately excluded: docs/ explains the standalone contract
    # by *naming* the projects we keep separate. Code is what matters.
    if ctx.suffix not in {"py", "ts", "tsx", "js", "jsx", "json", "yaml", "yml"}:
        return Decision.allow(HANDLER)
    # The harness's own tests AND the handler source contain forbidden-name
    # tokens by design (the deny-list itself, docstrings).
    if ctx.file_path is not None:
        posix = ctx.file_path.as_posix()
        if "/.claude/tests/" in posix or "/.claude/lib/handlers/" in posix:
            return Decision.allow(HANDLER)

    content = ctx.new_content

    path_hit = _PATH_PATTERN.search(content)
    if path_hit:
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why=f"Reference to external project '{path_hit.group('n')}' detected.",
            fix=(
                "This project is standalone. Recreate the pattern from scratch in "
                "this repo instead of pointing at a sibling."
            ),
            doc=DOC,
        )

    if ctx.suffix in {"py"}:
        for match in _PY_IMPORT.finditer(content):
            module = match.group("from") or match.group("import") or ""
            for chunk in module.split(","):
                name = chunk.strip().split(" as ", 1)[0]
                if name and _py_module_is_external(name):
                    return Decision.deny(
                        handler=HANDLER,
                        rule_id=RULE_ID,
                        why=f"Python import resolves to external project: {chunk!r}",
                        fix="Replace with a local module under `src/`.",
                        doc=DOC,
                    )

    if ctx.suffix in {"ts", "tsx", "js", "jsx"}:
        for match in _JS_IMPORT.finditer(content):
            if _js_path_is_external(match.group(1)):
                return Decision.deny(
                    handler=HANDLER,
                    rule_id=RULE_ID,
                    why=f"Import resolves to external project: {match.group(1)!r}",
                    fix="Replace with a local module under `src/`.",
                    doc=DOC,
                )

    return Decision.allow(HANDLER)
