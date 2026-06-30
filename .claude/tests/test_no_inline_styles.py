"""Tests for the no_inline_styles handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import no_inline_styles


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/tmp/X.svelte").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_no_style_attr() -> None:
    """Plain class-only markup passes."""
    assert no_inline_styles.check(_ctx("<div class='x'>y</div>")).severity == "allow"


def test_should_block_when_string_style_attr_present() -> None:
    """style="..." literal blocks."""
    assert no_inline_styles.check(_ctx('<div style="color: red">y</div>')).severity == "block"


def test_should_block_when_dynamic_style_attr_present() -> None:
    """style={...} dynamic also blocks."""
    assert no_inline_styles.check(_ctx("<div style={dynamic}>y</div>")).severity == "block"


def test_should_allow_when_svelte_style_directive_used() -> None:
    """Svelte's `style:--var=...` directive is the allowed escape hatch."""
    decision = no_inline_styles.check(_ctx('<div style:--color-foo="var(--color-accent)">y</div>'))
    assert decision.severity == "allow"


def test_should_block_when_unquoted_style_attr() -> None:
    """`style=color:red` (no quotes) is denied."""
    decision = no_inline_styles.check(_ctx("<div style=color:red>y</div>"))
    assert decision.severity == "block"


def test_should_block_when_bind_style_used() -> None:
    """`bind:style={...}` is denied — Svelte directive doesn't whitewash."""
    decision = no_inline_styles.check(_ctx("<div bind:style={dynamic}>y</div>"))
    assert decision.severity == "block"


def test_should_block_when_dom_style_assignment_in_script() -> None:
    """`el.style.color = ...` in a script block is denied."""
    code = "<script>function p(el) { el.style.color = 'red'; }</script>"
    assert no_inline_styles.check(_ctx(code)).severity == "block"


def test_should_block_when_dom_csstext_assignment() -> None:
    """`el.style.cssText = ...` is denied."""
    code = "<script>function p(el) { el.style.cssText = 'color: red'; }</script>"
    assert no_inline_styles.check(_ctx(code)).severity == "block"


def test_should_allow_when_style_directive_with_token() -> None:
    """`style:background={var(...)}` directive is allowed."""
    code = "<div style:background={`var(--color-${s})`}>y</div>"
    assert no_inline_styles.check(_ctx(code)).severity == "allow"
