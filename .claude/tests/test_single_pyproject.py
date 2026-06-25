"""Tests for the single_pyproject handler."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from lib import paths
from lib.context import HookContext
from lib.handlers import single_pyproject


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(paths, "REPO_ROOT", root)
    monkeypatch.setattr(single_pyproject, "REPO_ROOT", root)
    yield root


def _ctx(file_path: Path) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content="[project]\nname='x'\n",
        old_content=None,
    )


def _declare_workspace(root: Path, *packages: str) -> None:
    """Write a repo-root pnpm-workspace.yaml declaring the given package globs."""
    lines = "\n".join(f"  - '{p}'" for p in packages)
    (root / "pnpm-workspace.yaml").write_text(f"packages:\n{lines}\n")


def test_should_allow_pyproject_at_repo_root(repo: Path) -> None:
    """The root pyproject.toml is the one allowed home."""
    decision = single_pyproject.check(_ctx(repo / "pyproject.toml"))
    assert decision.severity == "allow"


def test_should_block_pyproject_in_subdir(repo: Path) -> None:
    """A second pyproject inside src/ would split the dep graph."""
    (repo / "src/backend").mkdir(parents=True)
    decision = single_pyproject.check(_ctx(repo / "src/backend/pyproject.toml"))
    assert decision.severity == "block"
    assert "pyproject.toml" in decision.why


def test_should_block_package_json_in_unregistered_subdir(repo: Path) -> None:
    """A package.json in a dir not declared in pnpm-workspace.yaml is blocked."""
    _declare_workspace(repo, "frontend")
    (repo / "src/backend").mkdir(parents=True)
    decision = single_pyproject.check(_ctx(repo / "src/backend/package.json"))
    assert decision.severity == "block"


def test_should_allow_package_json_in_declared_workspace_package(repo: Path) -> None:
    """A package.json in a pnpm-workspace-declared dir is the controlled exception."""
    _declare_workspace(repo, "frontend")
    (repo / "frontend").mkdir(parents=True)
    decision = single_pyproject.check(_ctx(repo / "frontend/package.json"))
    assert decision.severity == "allow"


def test_should_allow_tsconfig_in_declared_workspace_package(repo: Path) -> None:
    """tsconfig.json is workspace-scoped alongside package.json."""
    _declare_workspace(repo, "frontend")
    (repo / "frontend").mkdir(parents=True)
    decision = single_pyproject.check(_ctx(repo / "frontend/tsconfig.json"))
    assert decision.severity == "allow"


def test_should_block_lockfile_in_declared_workspace_package(repo: Path) -> None:
    """The lockfile stays root-only even inside a declared workspace package."""
    _declare_workspace(repo, "frontend")
    (repo / "frontend").mkdir(parents=True)
    decision = single_pyproject.check(_ctx(repo / "frontend/pnpm-lock.yaml"))
    assert decision.severity == "block"


def test_should_allow_dockerfile_in_deploy(repo: Path) -> None:
    """Dockerfile is allowed under deploy/."""
    (repo / "deploy/backend").mkdir(parents=True)
    decision = single_pyproject.check(_ctx(repo / "deploy/backend/Dockerfile"))
    assert decision.severity == "allow"


def test_should_block_dockerfile_in_random_subdir(repo: Path) -> None:
    """A Dockerfile sprinkled into a service dir is blocked."""
    (repo / "src/backend/api").mkdir(parents=True)
    decision = single_pyproject.check(_ctx(repo / "src/backend/api/Dockerfile"))
    assert decision.severity == "block"
