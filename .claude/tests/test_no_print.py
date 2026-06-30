"""Tests for the no_print handler."""

from __future__ import annotations

from pathlib import Path

import pytest
from lib import paths
from lib.context import HookContext
from lib.handlers import no_print


def _ctx(file_path: Path, content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    return repo


def test_should_block_when_print_in_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`print(` in src/backend/ is denied."""
    repo = _repo(tmp_path, monkeypatch)
    target = repo / "src/backend/x.py"
    target.parent.mkdir(parents=True)
    assert no_print.check(_ctx(target, "print('hi')")).severity == "block"


def test_should_allow_when_print_in_scripts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scripts may print freely."""
    repo = _repo(tmp_path, monkeypatch)
    target = repo / "scripts/util.py"
    target.parent.mkdir(parents=True)
    assert no_print.check(_ctx(target, "print('hi')")).severity == "allow"


def test_should_allow_when_print_in_tests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests may print freely."""
    repo = _repo(tmp_path, monkeypatch)
    target = repo / "tests/backend/test_x.py"
    target.parent.mkdir(parents=True)
    assert no_print.check(_ctx(target, "print('debug')")).severity == "allow"
