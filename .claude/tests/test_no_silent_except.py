"""Tests for the no_silent_except handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import no_silent_except


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/tmp/x.py").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_when_bare_except() -> None:
    """`except:` with nothing after is denied."""
    code = "try:\n    x()\nexcept:\n    pass\n"
    decision = no_silent_except.check(_ctx(code))
    assert decision.severity == "block"


def test_should_block_when_except_pass() -> None:
    """`except X: pass` is denied."""
    code = "try:\n    x()\nexcept ValueError:\n    pass\n"
    decision = no_silent_except.check(_ctx(code))
    assert decision.severity == "block"


def test_should_allow_when_except_handles_error() -> None:
    """A typed except with real handling passes."""
    code = "try:\n    x()\nexcept ValueError as e:\n    log.warning('bad', err=e)\n"
    decision = no_silent_except.check(_ctx(code))
    assert decision.severity == "allow"
