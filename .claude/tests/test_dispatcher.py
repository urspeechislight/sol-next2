"""Tests for the dispatcher chain."""

from __future__ import annotations

import json

import pytest
from lib import dispatcher
from lib.context import HookContext
from lib.decision import Decision


def test_should_allow_when_no_handler_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty advisory chain → exit 0."""
    monkeypatch.setattr("sys.stdin", _StringIn("{}"))
    with pytest.raises(SystemExit) as exc:
        dispatcher.run(event="test", handlers=[])
    assert exc.value.code == 0


def test_should_exit_two_when_handler_blocks(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """First deny → exit 2, structured envelope on stderr."""
    monkeypatch.setattr("sys.stdin", _StringIn("{}"))

    def deny_handler(_ctx: HookContext) -> Decision:
        return Decision.deny(handler="t", rule_id="X", why="nope", fix="do it differently")

    with pytest.raises(SystemExit) as exc:
        dispatcher.run(event="test", handlers=[deny_handler])
    assert exc.value.code == 2

    captured = capsys.readouterr()
    first_line = captured.err.splitlines()[0]
    envelope = json.loads(first_line)
    assert envelope["type"] == "harness.block"
    assert envelope["rule_id"] == "X"


def test_should_treat_handler_crash_as_deny(monkeypatch: pytest.MonkeyPatch) -> None:
    """A handler exception is a deny, not a silent allow."""
    monkeypatch.setattr("sys.stdin", _StringIn("{}"))

    def boom(_ctx: HookContext) -> Decision:
        raise RuntimeError("boom")

    with pytest.raises(SystemExit) as exc:
        dispatcher.run(event="test", handlers=[boom])
    assert exc.value.code == 2


class _StringIn:
    def __init__(self, content: str) -> None:
        self._content = content

    def read(self) -> str:
        return self._content
