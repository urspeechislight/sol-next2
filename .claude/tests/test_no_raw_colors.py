"""Tests for the no_raw_colors handler."""

from __future__ import annotations

from pathlib import Path

import pytest
from lib import paths
from lib.context import HookContext
from lib.handlers import no_raw_colors


def _ctx(file_path: Path, content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_no_raw_colors_present(tmp_path: Path) -> None:
    """Passes when content uses only token-backed classes."""
    f = tmp_path / "Comp.svelte"
    decision = no_raw_colors.check(_ctx(f, "<div class='bg-accent'>x</div>"))
    assert decision.severity == "allow"


def test_should_block_when_hex_color_in_component(tmp_path: Path) -> None:
    """Hex literals in a component are denied."""
    f = tmp_path / "Comp.svelte"
    decision = no_raw_colors.check(_ctx(f, "<div style='color: #abc'>x</div>"))
    assert decision.severity == "block"
    assert decision.rule_id == "DS-001"


def test_should_block_when_oklch_function_outside_tokens(tmp_path: Path) -> None:
    """oklch() outside tokens.css is denied."""
    f = tmp_path / "Comp.svelte"
    decision = no_raw_colors.check(_ctx(f, "color: oklch(0.5 0.1 200)"))
    assert decision.severity == "block"


def test_should_allow_when_writing_to_tokens_css(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The token SSOT file IS allowed to contain raw colors."""
    repo = tmp_path / "repo"
    target = repo / "src/frontend/lib/design-system/tokens.css"
    target.parent.mkdir(parents=True)
    target.write_text("")
    monkeypatch.setattr(paths, "REPO_ROOT", repo)

    decision = no_raw_colors.check(_ctx(target, "--c: oklch(0.5 0.1 200);"))
    assert decision.severity == "allow"
