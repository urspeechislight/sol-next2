"""Tests for the primitive_usage handler."""

from __future__ import annotations

from pathlib import Path

import pytest
from lib import paths
from lib.context import HookContext
from lib.handlers import primitive_usage


def _ctx(file_path: Path, content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def _make_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    return repo


def test_should_block_when_raw_button_in_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Raw <button> in a route is denied."""
    repo = _make_repo(tmp_path, monkeypatch)
    target = repo / "src/frontend/routes/+page.svelte"
    target.parent.mkdir(parents=True)
    decision = primitive_usage.check(_ctx(target, "<button>Click</button>"))
    assert decision.severity == "block"
    assert decision.rule_id == "DS-003"


def test_should_allow_when_raw_button_in_design_system(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The design system itself uses raw <button>."""
    repo = _make_repo(tmp_path, monkeypatch)
    target = repo / "src/frontend/lib/design-system/primitives/Button.svelte"
    target.parent.mkdir(parents=True)
    decision = primitive_usage.check(_ctx(target, "<button>Click</button>"))
    assert decision.severity == "allow"


def test_should_allow_when_input_outside_frontend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Other places (docs, scripts) aren't enforced."""
    repo = _make_repo(tmp_path, monkeypatch)
    target = repo / "scripts/util.svelte"
    target.parent.mkdir(parents=True)
    decision = primitive_usage.check(_ctx(target, "<input />"))
    assert decision.severity == "allow"
