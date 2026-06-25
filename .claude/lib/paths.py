"""Project path helpers used by handlers.

Centralizes the rules for "what directory am I editing?" so handlers don't
duplicate path logic.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any, cast

import yaml

# The repo root. ``.claude/lib/paths.py`` -> ``.claude/lib`` -> ``.claude`` -> repo.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Harness-side SSOT for the pnpm workspace package globs.
#
# The real source of truth is the repo-root ``pnpm-workspace.yaml``. The laptop
# launchpoint is a stub: that manifest lives only on buildhost, so the laptop-side
# ``ssh_remote_write`` validator (which re-runs this handler chain against the
# laptop-equivalent path) cannot read it. ``STUB_WORKSPACE_GLOBS`` mirrors the
# declared package list so both sides agree; ``tests/test_workspace_globs.py``
# pins it equal to the real manifest on buildhost, so the two cannot drift.
STUB_WORKSPACE_GLOBS: tuple[str, ...] = ("src/frontend", "frontend")

_WORKSPACE_MANIFEST = "pnpm-workspace.yaml"


def workspace_globs() -> tuple[str, ...]:
    """Declared pnpm workspace package globs.

    Reads the repo-root ``pnpm-workspace.yaml`` when present (buildhost in-session),
    falling back to the mirrored ``STUB_WORKSPACE_GLOBS`` on the laptop stub
    where that manifest is absent. A present-but-malformed manifest yields no
    globs, so a broken workspace file fails closed rather than exempting paths.
    """
    manifest = REPO_ROOT / _WORKSPACE_MANIFEST
    if not manifest.exists():
        return STUB_WORKSPACE_GLOBS
    raw_any: Any = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    if not isinstance(raw_any, dict):
        return ()
    data = cast(dict[str, Any], raw_any)
    packages_any: Any = data.get("packages")
    if not isinstance(packages_any, list):
        return ()
    packages = cast(list[Any], packages_any)
    return tuple(entry for entry in packages if isinstance(entry, str))


def is_declared_package_dir(parent: str) -> bool:
    """True when ``parent`` (a repo-relative dir) matches a workspace package glob."""
    return any(fnmatch.fnmatch(parent, glob) for glob in workspace_globs())


def is_in(path: Path | None, *segments: str) -> bool:
    """True if ``path`` is inside any of the given repo-relative segments.

    Examples::

        is_in(p, "src/frontend/lib")           # one segment
        is_in(p, "src/backend", "src/pipeline") # any of several
    """
    if path is None:
        return False
    try:
        rel = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return False
    rel_str = rel.as_posix()
    return any(rel_str.startswith(seg.rstrip("/") + "/") or rel_str == seg for seg in segments)


def relpath(path: Path | None) -> str:
    """Return the path relative to the repo root (or absolute string fallback)."""
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def is_design_token_file(path: Path | None) -> bool:
    """True if this path is the design tokens SSOT — these files may use raw colors."""
    return (
        is_in(path, "src/frontend/tokens.css")
        or is_in(path, "src/frontend/lib/design-system/tokens.css")
        or is_in(path, "src/frontend/lib/design-system/internal")
    )
