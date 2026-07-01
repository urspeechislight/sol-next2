"""Tests for the no_inline_comments handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import no_inline_comments


def _ctx(file_path: Path, content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_when_inline_comment_present(tmp_path: Path) -> None:
    """Code followed by a comment on the same line is denied."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    assert no_inline_comments.check(_ctx(target, "x = 1  # set x\n")).severity == "block"


def test_should_block_when_standalone_comment_present(tmp_path: Path) -> None:
    """A comment on its own line is denied."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    assert no_inline_comments.check(_ctx(target, "# explain\nx = 1\n")).severity == "block"


def test_should_allow_when_comment_is_directive(tmp_path: Path) -> None:
    """Tooling directives like `# type: ignore` are allowed."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    assert no_inline_comments.check(_ctx(target, "x = y  # type: ignore[assignment]\n")).severity == "allow"


def test_should_allow_when_comment_is_pyright_directive(tmp_path: Path) -> None:
    """The pyright type-checker directive `# pyright: ignore[...]` is allowed."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    code = "return Settings()  # pyright: ignore[reportCallIssue]\n"
    assert no_inline_comments.check(_ctx(target, code)).severity == "allow"


def test_should_allow_when_line_has_unicode_escape(tmp_path: Path) -> None:
    """Lines carrying a \\u escape (Arabic maps) may annotate the glyph."""
    target = tmp_path / "src/utils/text.py"
    target.parent.mkdir(parents=True)
    code = 'MAP = {"\\u0623": "\\u0627"}  # gloss\n'
    assert no_inline_comments.check(_ctx(target, code)).severity == "allow"


def test_should_allow_when_hash_is_inside_string(tmp_path: Path) -> None:
    """A `#` inside a string literal is not a comment."""
    target = tmp_path / "src/utils/x.py"
    target.parent.mkdir(parents=True)
    assert no_inline_comments.check(_ctx(target, 'tag = "#hashtag"\n')).severity == "allow"
