"""Tests for the function_size_cap handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import function_size_cap


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/tmp/x.py").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_function_under_limit() -> None:
    """A short function passes."""
    body = "    return 1\n"
    decision = function_size_cap.check(_ctx(f"def f():\n{body}"))
    assert decision.severity == "allow"


def test_should_block_when_function_too_long() -> None:
    """An 100-line function denies."""
    body = "\n".join(f"    x = {i}" for i in range(100))
    decision = function_size_cap.check(_ctx(f"def big():\n{body}\n"))
    assert decision.severity == "block"
    assert "big" in decision.why


def test_should_allow_when_short_async_function() -> None:
    """Short async function passes."""
    decision = function_size_cap.check(_ctx("async def f():\n    return 1\n"))
    assert decision.severity == "allow"
