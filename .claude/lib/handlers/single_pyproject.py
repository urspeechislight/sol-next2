"""Block creation of additional dependency-manifest files outside the repo root.

Why: a monorepo with two ``pyproject.toml`` files (or two ``package.json``
files outside an intentional pnpm workspace) splits the dependency graph
into "us" and "them." One side upgrades a library; the other does not;
their behaviours diverge silently. The user's SSOT rule applies to
*build configuration* as much as it does to constants.

Allowed locations:

  * ``pyproject.toml`` at the repo root only.
  * ``package.json`` and ``tsconfig.json`` at the repo root, or in any
    directory declared as a package in the repo-root ``pnpm-workspace.yaml``.
    The single lockfile (``pnpm-lock.yaml``, ``uv.lock``), the workspace
    manifest itself, and the toolchain pins (``.python-version``, ``.nvmrc``)
    stay root-only even inside a workspace.
  * ``Dockerfile`` / ``docker-compose.yml`` at the repo root or under
    ``deploy/``.

Block when the agent tries to Write/Edit any of these at a non-allowed
path. This catches "let me just add a new pyproject for this subdir"
before it lands.
"""

from __future__ import annotations

from pathlib import Path

from ..context import HookContext
from ..decision import Decision
from ..paths import REPO_ROOT, is_declared_package_dir

HANDLER = "single_pyproject"
RULE_ID = "BUILD-001"
DOC = "docs/quality-standards.md#ssot-dry"

# Files that must live at the repo root only.
_ROOT_ONLY: frozenset[str] = frozenset(
    {
        "pyproject.toml",
        "uv.lock",
        "package.json",
        "pnpm-workspace.yaml",
        "pnpm-lock.yaml",
        "tsconfig.json",
        ".python-version",
        ".nvmrc",
    }
)

# Of the root-only set, the manifests a pnpm-workspace-declared sub-package
# legitimately owns. The lockfile, workspace manifest, and toolchain pins are
# deliberately excluded: they stay singular at the root to keep one dep graph.
_WORKSPACE_SCOPED: frozenset[str] = frozenset({"package.json", "tsconfig.json"})

# Files that may live at the root *or* under designated deploy dirs.
_DEPLOY_FILES: frozenset[str] = frozenset(
    {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}
)
_DEPLOY_ROOTS: tuple[str, ...] = ("deploy", "infra")


def _relative_to_repo(path: Path) -> Path | None:
    """Return path relative to REPO_ROOT, or None if it's outside the repo."""
    resolved = path.resolve()
    if not resolved.is_relative_to(REPO_ROOT):
        return None
    return resolved.relative_to(REPO_ROOT)


def check(ctx: HookContext) -> Decision:
    """Block dependency/build manifest files outside their allowed homes."""
    if not ctx.is_write or ctx.file_path is None:
        return Decision.allow(HANDLER)
    rel = _relative_to_repo(ctx.file_path)
    if rel is None:
        return Decision.allow(HANDLER)

    name = rel.name
    parent = rel.parent.as_posix()
    is_at_root = parent == "."

    if name in _ROOT_ONLY and not is_at_root:
        if name in _WORKSPACE_SCOPED and is_declared_package_dir(parent):
            return Decision.allow(HANDLER)
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why=(
                f"`{name}` must live only at the repo root; this write would "
                f"create it at `{rel.as_posix()}`."
            ),
            fix=(
                f"Edit the existing repo-root `{name}` instead. If you genuinely "
                "need to scope dependencies for a sub-package, declare its "
                "directory in the repo-root `pnpm-workspace.yaml` (one root "
                "lockfile, one package.json + tsconfig per declared package), "
                "not a parallel manifest with its own lockfile."
            ),
            doc=DOC,
        )

    if (
        name in _DEPLOY_FILES
        and not is_at_root
        and not any(parent == r or parent.startswith(r + "/") for r in _DEPLOY_ROOTS)
    ):
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why=(
                f"`{name}` must live at the repo root or under {'/'.join(_DEPLOY_ROOTS)}/; "
                f"this write would create it at `{rel.as_posix()}`."
            ),
            fix=(
                "Move the file to `deploy/` (or the repo root). Multiple "
                "Dockerfiles scattered across the tree make the deploy story "
                "impossible to audit."
            ),
            doc=DOC,
        )
    return Decision.allow(HANDLER)
