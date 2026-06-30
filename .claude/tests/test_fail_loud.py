"""Tests for the fail_loud handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import fail_loud


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/tmp/x.py").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_when_except_returns_none_without_log() -> None:
    """`return None` in except without logging is a silent fallback."""
    code = (
        "def fn() -> str | None:\n"
        "    try:\n"
        "        return parse()\n"
        "    except ValueError:\n"
        "        return None\n"
    )
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "block"
    assert "return None" in decision.why


def test_should_block_when_except_returns_empty_list_without_log() -> None:
    """`return []` in except without logging is a silent fallback."""
    code = (
        "def fn() -> list[int]:\n"
        "    try:\n"
        "        return parse()\n"
        "    except ValueError:\n"
        "        return []\n"
    )
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "block"


def test_should_block_when_except_returns_empty_dict_without_log() -> None:
    """`return {}` in except without logging is a silent fallback."""
    code = (
        "def fn() -> dict[str, int]:\n"
        "    try:\n"
        "        return parse()\n"
        "    except ValueError:\n"
        "        return {}\n"
    )
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "block"


def test_should_block_when_except_returns_placeholder_string() -> None:
    """`return 'UNKNOWN'` is a placeholder string that lies to callers."""
    code = (
        "def fn() -> str:\n"
        "    try:\n"
        "        return parse()\n"
        "    except ValueError:\n"
        "        return 'UNKNOWN'\n"
    )
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "block"


def test_should_block_when_except_continues_without_log() -> None:
    """`continue` in except without logging is silent."""
    code = (
        "def fn() -> None:\n"
        "    for x in []:\n"
        "        try:\n"
        "            parse(x)\n"
        "        except ValueError:\n"
        "            continue\n"
    )
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "block"


def test_should_block_when_except_body_is_pass_only() -> None:
    """`except X: pass` is silent."""
    code = "try:\n    x()\nexcept ValueError:\n    pass\n"
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "block"


def test_should_allow_when_logger_called_before_return_none() -> None:
    """Logging before returning is loud — the failure is visible."""
    code = (
        "def fn() -> str | None:\n"
        "    try:\n"
        "        return parse()\n"
        "    except ValueError as e:\n"
        "        logger.error('parse failed', exc_info=True)\n"
        "        return None\n"
    )
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "allow"


def test_should_allow_when_self_logger_called_before_continue() -> None:
    """Self-rooted logging counts as loud."""
    code = (
        "class C:\n"
        "    def run(self) -> None:\n"
        "        for x in []:\n"
        "            try:\n"
        "                parse(x)\n"
        "            except ValueError as e:\n"
        "                self.logger.warning('skipping', err=e)\n"
        "                continue\n"
    )
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "allow"


def test_should_allow_when_raise_before_silent_pattern() -> None:
    """A raise inside the handler means we never reach the silent line."""
    code = (
        "def fn() -> None:\n"
        "    try:\n"
        "        parse()\n"
        "    except ValueError as e:\n"
        "        raise RuntimeError('wrap') from e\n"
        "        return None\n"
    )
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "allow"


def test_should_allow_when_explicit_return_value() -> None:
    """Returning a typed Result / explicit failure value is fine."""
    code = (
        "def fn() -> int:\n"
        "    try:\n"
        "        return parse()\n"
        "    except ValueError:\n"
        "        return 7\n"
    )
    decision = fail_loud.check(_ctx(code))
    assert decision.severity == "allow"
