"""Tests for the variants_only handler."""

from __future__ import annotations

from pathlib import Path

import pytest
from lib import paths
from lib.context import HookContext
from lib.handlers import variants_only


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


def test_should_block_when_inline_status_map_in_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A status-keyed object literal in a route is denied."""
    repo = _make_repo(tmp_path, monkeypatch)
    target = repo / "src/frontend/routes/page.svelte"
    target.parent.mkdir(parents=True)
    code = (
        "const palette = {\n"
        "  success: 'green',\n"
        "  warning: 'yellow',\n"
        "  danger: 'red',\n"
        "  info: 'blue',\n"
        "};\n"
    )
    decision = variants_only.check(_ctx(target, code))
    assert decision.severity == "block"


def test_should_allow_when_in_design_system(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The variants.ts file is the SSOT — it's allowed to declare these."""
    repo = _make_repo(tmp_path, monkeypatch)
    target = repo / "src/frontend/lib/design-system/variants.ts"
    target.parent.mkdir(parents=True)
    code = (
        "const palette = {\n"
        "  success: 'green',\n"
        "  warning: 'yellow',\n"
        "  danger: 'red',\n"
        "  info: 'blue',\n"
        "};\n"
    )
    decision = variants_only.check(_ctx(target, code))
    assert decision.severity == "allow"


def test_should_allow_when_unrelated_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An object missing the status keys passes."""
    repo = _make_repo(tmp_path, monkeypatch)
    target = repo / "src/frontend/routes/page.svelte"
    target.parent.mkdir(parents=True)
    code = "const config = { host: 'x', port: 8000 };\n"
    decision = variants_only.check(_ctx(target, code))
    assert decision.severity == "allow"
