"""Tests for the helper_constraints handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import helper_constraints


def _ctx(file_path: Path, content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_when_name_is_vague(tmp_path: Path) -> None:
    """A vague function name like `process` is denied."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    assert helper_constraints.check(_ctx(target, "def process() -> int:\n    return 1\n")).severity == "block"


def test_should_block_when_name_has_multiple_responsibilities(tmp_path: Path) -> None:
    """A `_and_` name signals multiple responsibilities and is denied."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    code = "def parse_and_validate() -> int:\n    return 1\n"
    assert helper_constraints.check(_ctx(target, code)).severity == "block"


def test_should_block_when_name_is_too_long(tmp_path: Path) -> None:
    """A name longer than 40 chars is denied."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    long_name = "extract_" + "x" * 40
    code = f"def {long_name}() -> int:\n    return 1\n"
    assert helper_constraints.check(_ctx(target, code)).severity == "block"


def test_should_block_when_too_many_params(tmp_path: Path) -> None:
    """More than 5 parameters is denied."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    code = "def f(a: int, b: int, c: int, d: int, e: int, g: int) -> int:\n    return 1\n"
    assert helper_constraints.check(_ctx(target, code)).severity == "block"


def test_should_allow_when_function_is_clean(tmp_path: Path) -> None:
    """A focused, well-named function within limits is allowed."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    code = "def extract_isnad(a: int, b: int) -> int:\n    return a + b\n"
    assert helper_constraints.check(_ctx(target, code)).severity == "allow"


def test_should_allow_when_self_not_counted_toward_limit(tmp_path: Path) -> None:
    """`self` does not count toward the parameter limit."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    code = (
        "class C:\n"
        "    def m(self, a: int, b: int, c: int, d: int, e: int) -> int:\n"
        "        return a\n"
    )
    assert helper_constraints.check(_ctx(target, code)).severity == "allow"
