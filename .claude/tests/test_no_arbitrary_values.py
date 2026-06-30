"""Tests for the no_arbitrary_values handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import no_arbitrary_values


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/tmp/x.svelte").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_when_text_arbitrary_with_px() -> None:
    """`text-[14px]` is denied."""
    assert no_arbitrary_values.check(_ctx("<div class='text-[14px]'/>")).severity == "block"


def test_should_block_when_padding_arbitrary_rem() -> None:
    """`p-[3rem]` is denied."""
    assert no_arbitrary_values.check(_ctx("<div class='p-[3rem]'/>")).severity == "block"


def test_should_block_when_width_arbitrary_pct() -> None:
    """`w-[42%]` is denied."""
    assert no_arbitrary_values.check(_ctx("<div class='w-[42%]'/>")).severity == "block"


def test_should_allow_when_arbitrary_uses_var() -> None:
    """`p-[var(--spacing-foo)]` is the documented escape hatch."""
    decision = no_arbitrary_values.check(_ctx("<div class='p-[var(--spacing-4)]'/>"))
    assert decision.severity == "allow"


def test_should_allow_when_text_uses_length_var() -> None:
    """Tailwind 4 length syntax: `text-[length:var(--text-lg)]`."""
    decision = no_arbitrary_values.check(_ctx("<div class='text-[length:var(--text-lg)]'/>"))
    assert decision.severity == "allow"


def test_should_allow_when_no_arbitrary_value() -> None:
    """Plain token utilities pass."""
    decision = no_arbitrary_values.check(_ctx("<div class='text-lg p-4 rounded-md'/>"))
    assert decision.severity == "allow"
