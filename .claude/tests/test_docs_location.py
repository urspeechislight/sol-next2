"""Tests for the docs_location handler."""

from __future__ import annotations

from pathlib import Path

import pytest
from lib import paths
from lib.context import HookContext
from lib.handlers import docs_location


def _ctx(file_path: Path, content: str = "# x") -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_writing_to_docs_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Files inside docs/ pass."""
    repo = tmp_path / "repo"
    target = repo / "docs/architecture.md"
    target.parent.mkdir(parents=True)
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    assert docs_location.check(_ctx(target)).severity == "allow"


def test_should_allow_root_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Root README.md is allowed (entry point)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    assert docs_location.check(_ctx(repo / "README.md")).severity == "allow"


def test_should_block_when_md_in_lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A README inside lib/ is rejected — must move to docs/."""
    repo = tmp_path / "repo"
    target = repo / "frontend/src/lib/design-system/README.md"
    target.parent.mkdir(parents=True)
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    assert docs_location.check(_ctx(target)).severity == "block"


def test_should_allow_subagent_definition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Subagent defs under .claude/agents/ are capability config, not docs."""
    repo = tmp_path / "repo"
    target = repo / ".claude/agents/manuscript-auditor.md"
    target.parent.mkdir(parents=True)
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    assert docs_location.check(_ctx(target)).severity == "allow"


def test_should_allow_skill_definition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SKILL.md bundles under .claude/skills/ are capability config, not docs."""
    repo = tmp_path / "repo"
    target = repo / ".claude/skills/serve-book/SKILL.md"
    target.parent.mkdir(parents=True)
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    assert docs_location.check(_ctx(target)).severity == "allow"


def test_should_block_stray_markdown_in_claude_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Carve-out stays narrow: stray .md elsewhere under .claude/ is still blocked."""
    repo = tmp_path / "repo"
    target = repo / ".claude/notes.md"
    target.parent.mkdir(parents=True)
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    assert docs_location.check(_ctx(target)).severity == "block"
