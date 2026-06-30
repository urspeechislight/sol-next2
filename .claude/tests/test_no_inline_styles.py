"""Tests for the no_inline_styles handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import no_inline_styles


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/tmp/X.tsx").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_no_style_attr() -> None:
    """Plain className-only markup passes."""
    assert no_inline_styles.check(_ctx('<div className="x">y</div>')).severity == "allow"


def test_should_block_when_string_style_attr_present() -> None:
    """style="..." literal blocks."""
    assert no_inline_styles.check(_ctx('<div style="color: red">y</div>')).severity == "block"


def test_should_block_when_jsx_object_style_present() -> None:
    """The canonical React style={{ ... }} blocks."""
    decision = no_inline_styles.check(_ctx("<div style={{ color: 'red' }}>y</div>"))
    assert decision.severity == "block"


def test_should_block_when_dynamic_style_attr_present() -> None:
    """style={expr} dynamic also blocks."""
    assert no_inline_styles.check(_ctx("<div style={dynamic}>y</div>")).severity == "block"


def test_should_allow_when_style_is_a_spaced_variable() -> None:
    """A `const style = {...}` variable (spaced =) is not a JSX inline style."""
    code = "const style = { color: theme.fg };\nexport const x = style;"
    assert no_inline_styles.check(_ctx(code)).severity == "allow"


def test_should_block_when_dom_style_assignment() -> None:
    """`el.style.color = ...` is denied."""
    code = "function p(el: HTMLElement) { el.style.color = 'red'; }"
    assert no_inline_styles.check(_ctx(code)).severity == "block"


def test_should_block_when_dom_csstext_assignment() -> None:
    """`el.style.cssText = ...` is denied."""
    code = "function p(el: HTMLElement) { el.style.cssText = 'color: red'; }"
    assert no_inline_styles.check(_ctx(code)).severity == "block"
