"""Tests for the docstring_required handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import docstring_required


def _ctx(file_path: Path, content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_when_public_function_lacks_docstring(tmp_path: Path) -> None:
    """A public function with no docstring is denied."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    assert docstring_required.check(_ctx(target, "def parse() -> int:\n    return 1\n")).severity == "block"


def test_should_block_when_public_class_lacks_docstring(tmp_path: Path) -> None:
    """A public class with no docstring is denied."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    assert docstring_required.check(_ctx(target, "class Thing:\n    pass\n")).severity == "block"


def test_should_allow_when_function_has_docstring(tmp_path: Path) -> None:
    """A documented public function is allowed."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    code = 'def parse() -> int:\n    """Parse."""\n    return 1\n'
    assert docstring_required.check(_ctx(target, code)).severity == "allow"


def test_should_allow_when_function_is_private(tmp_path: Path) -> None:
    """A private function without a docstring is allowed."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    assert docstring_required.check(_ctx(target, "def _helper() -> int:\n    return 1\n")).severity == "allow"


def test_should_allow_when_file_is_test(tmp_path: Path) -> None:
    """Test files are exempt."""
    target = tmp_path / "tests/test_x.py"
    target.parent.mkdir(parents=True)
    assert docstring_required.check(_ctx(target, "def test_x() -> None:\n    assert True\n")).severity == "allow"
