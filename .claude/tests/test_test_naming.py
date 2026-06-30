"""Tests for the test_naming handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import test_naming


def _ctx(file_path: Path, content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_python_test_follows_convention(tmp_path: Path) -> None:
    """`test_should_VERB_OBJECT_CONDITION` passes."""
    f = tmp_path / "test_x.py"
    code = "def test_should_return_zero_when_input_is_empty():\n    pass\n"
    assert test_naming.check(_ctx(f, code)).severity == "allow"


def test_should_block_when_python_test_uses_generic_name(tmp_path: Path) -> None:
    """`test_thing_works` style is denied."""
    f = tmp_path / "test_x.py"
    code = "def test_thing_works():\n    pass\n"
    assert test_naming.check(_ctx(f, code)).severity == "block"


def test_should_allow_when_ts_test_uses_should_prefix(tmp_path: Path) -> None:
    """`should_X_Y` style in TS passes."""
    f = tmp_path / "x.test.ts"
    code = "test('should_apply_base_class', () => {});\n"
    assert test_naming.check(_ctx(f, code)).severity == "allow"


def test_should_block_when_ts_test_uses_describe_form(tmp_path: Path) -> None:
    """Generic TS test name is denied."""
    f = tmp_path / "x.test.ts"
    code = "test('renders correctly', () => {});\n"
    assert test_naming.check(_ctx(f, code)).severity == "block"


def test_should_allow_when_ts_test_uses_camel_case(tmp_path: Path) -> None:
    """`shouldRenderButton` camelCase passes."""
    f = tmp_path / "x.test.ts"
    code = "test('shouldRenderButtonWhenLoading', () => {});\n"
    assert test_naming.check(_ctx(f, code)).severity == "allow"


def test_should_allow_when_ts_test_uses_sentence_form(tmp_path: Path) -> None:
    """`should render button when loading` sentence form passes."""
    f = tmp_path / "x.test.ts"
    code = "test('should render button when loading', () => {});\n"
    assert test_naming.check(_ctx(f, code)).severity == "allow"


def test_should_block_when_ts_test_lacks_predicate(tmp_path: Path) -> None:
    """Bare `should` with nothing after is denied."""
    f = tmp_path / "x.test.ts"
    code = "test('should', () => {});\n"
    assert test_naming.check(_ctx(f, code)).severity == "block"
