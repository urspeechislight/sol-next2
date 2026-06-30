"""Tests for the import_boundaries handler."""

from __future__ import annotations

from pathlib import Path

import pytest
from lib import paths
from lib.context import HookContext
from lib.handlers import import_boundaries


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


def test_should_block_when_route_imports_internal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A route reaching into design-system/internal is denied."""
    repo = _make_repo(tmp_path, monkeypatch)
    target = repo / "src/frontend/routes/+page.svelte"
    target.parent.mkdir(parents=True)
    code = "import { thing } from '$lib/design-system/internal';\n"
    decision = import_boundaries.check(_ctx(target, code))
    assert decision.severity == "block"


def test_should_allow_when_design_system_imports_internal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The design system itself may use internal/."""
    repo = _make_repo(tmp_path, monkeypatch)
    target = repo / "src/frontend/lib/design-system/primitives/X.svelte"
    target.parent.mkdir(parents=True)
    code = "import { thing } from '$lib/design-system/internal';\n"
    decision = import_boundaries.check(_ctx(target, code))
    assert decision.severity == "allow"


def test_should_block_when_frontend_imports_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Frontend importing the Python backend package is denied."""
    repo = _make_repo(tmp_path, monkeypatch)
    target = repo / "src/frontend/routes/+page.ts"
    target.parent.mkdir(parents=True)
    code = "import { x } from 'backend/something';\n"
    decision = import_boundaries.check(_ctx(target, code))
    assert decision.severity == "block"
