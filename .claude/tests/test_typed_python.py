"""Tests for the typed_python handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import typed_python


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/tmp/x.py").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_when_public_function_missing_return_type() -> None:
    """Public function with no `-> T` is denied."""
    decision = typed_python.check(_ctx("def hello(name):\n    return name\n"))
    assert decision.severity == "block"


def test_should_allow_when_public_function_has_return_type() -> None:
    """Annotated function passes."""
    decision = typed_python.check(_ctx("def hello(name: str) -> str:\n    return name\n"))
    assert decision.severity == "allow"


def test_should_allow_when_function_is_private() -> None:
    """`_private` functions are exempt."""
    decision = typed_python.check(_ctx("def _internal(x):\n    return x\n"))
    assert decision.severity == "allow"


def test_should_allow_when_async_function_typed() -> None:
    """Annotated async passes."""
    decision = typed_python.check(_ctx("async def f() -> int:\n    return 1\n"))
    assert decision.severity == "allow"
