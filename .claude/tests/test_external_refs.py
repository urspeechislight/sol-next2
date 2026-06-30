"""Tests for the external_refs (standalone-isolation) handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import external_refs


def _ctx(content: str, suffix: str = "py") -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path(f"/tmp/x.{suffix}").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_when_referencing_sibling_project_path() -> None:
    """Path to a sibling project is denied."""
    decision = external_refs.check(_ctx("PATH = '/home/dev/code/sol-next/src'"))
    assert decision.severity == "block"


def test_should_block_when_referencing_another_sol_project_path() -> None:
    """A path to another sol-* sibling is denied too."""
    decision = external_refs.check(_ctx("# see ~/code/sol-codex/ui"))
    assert decision.severity == "block"


def test_should_load_private_banned_names_from_the_local_file(tmp_path: Path) -> None:
    """Names in the gitignored local file are loaded as extra bans."""
    f = tmp_path / "external_refs.private"
    f.write_text("acme-internal\n# a comment\n\nfoo-bar\n")
    assert external_refs.load_private_refs(f) == ("acme-internal", "foo-bar")


def test_should_allow_when_no_external_reference() -> None:
    """Local-only paths pass."""
    decision = external_refs.check(_ctx("from backend.core import settings"))
    assert decision.severity == "allow"
