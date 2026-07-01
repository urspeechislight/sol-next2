"""Tests for the file_size_cap handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import file_size_cap


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/tmp/x.py").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_file_is_small() -> None:
    """A 50-line file passes."""
    decision = file_size_cap.check(_ctx("line\n" * 50))
    assert decision.severity == "allow"


def test_should_allow_when_file_under_warn_cap() -> None:
    """A 350-line file is still under the 400-LOC soft limit."""
    decision = file_size_cap.check(_ctx("x = 1\n" * 350))
    assert decision.severity == "allow"


def test_should_advise_when_file_above_warn_cap() -> None:
    """A 420-line file emits an advisory but allows."""
    decision = file_size_cap.check(_ctx("x = 1\n" * 420))
    assert decision.severity == "advisory"


def test_should_advise_when_file_at_former_hard_cap() -> None:
    """A 450-LOC file advises; the cap is a signal, not a block."""
    decision = file_size_cap.check(_ctx("x = 1\n" * 450))
    assert decision.severity == "advisory"
    assert decision.rule_id == "QUAL-010"


def test_should_advise_when_file_far_above_signal() -> None:
    """A 600-line file still advises rather than blocks."""
    decision = file_size_cap.check(_ctx("x = 1\n" * 600))
    assert decision.severity == "advisory"
    assert decision.rule_id == "QUAL-010"
