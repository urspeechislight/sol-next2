"""Tests for the magic_numbers handler."""

from __future__ import annotations

from pathlib import Path

import pytest
from lib import paths
from lib.context import HookContext
from lib.handlers import magic_numbers


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


def test_should_block_when_magic_number_in_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A literal not in {-1,0,1,2,100} is blocked in production code."""
    repo = _repo(tmp_path, monkeypatch)
    target = repo / "src/backend/x.py"
    target.parent.mkdir(parents=True)
    code = "def f():\n    return retry(3600)\n"
    assert magic_numbers.check(_ctx(target, code)).severity == "block"


def test_should_allow_when_only_whitelisted_literals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`-1`, `0`, `1`, `2`, `100` are fine bare."""
    repo = _repo(tmp_path, monkeypatch)
    target = repo / "src/backend/x.py"
    target.parent.mkdir(parents=True)
    code = "def f():\n    return [0, 1, 2, -1, 100]\n"
    assert magic_numbers.check(_ctx(target, code)).severity == "allow"


def test_should_allow_when_constants_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`constants.py` is the home of magic values; allowed."""
    repo = _repo(tmp_path, monkeypatch)
    target = repo / "src/backend/core/constants.py"
    target.parent.mkdir(parents=True)
    code = "MAX_RETRIES = 3600\n"
    assert magic_numbers.check(_ctx(target, code)).severity == "allow"


def test_should_allow_when_outside_production(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tests may use any literal."""
    repo = _repo(tmp_path, monkeypatch)
    target = repo / "tests/backend/test_x.py"
    target.parent.mkdir(parents=True)
    code = "def test_should_pass_when_x():\n    assert 42 == 42\n"
    assert magic_numbers.check(_ctx(target, code)).severity == "allow"


def test_should_allow_when_literal_in_type_annotation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`Literal[200]` is exempt — annotations are allowed to carry constants."""
    repo = _repo(tmp_path, monkeypatch)
    target = repo / "src/backend/x.py"
    target.parent.mkdir(parents=True)
    code = "from typing import Literal\n\ndef f() -> Literal[200]:\n    return 1\n"
    assert magic_numbers.check(_ctx(target, code)).severity == "allow"
