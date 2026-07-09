"""Tests for the post_ruff handler.

post_ruff runs the real ruff binary against the just-written Python file and
downgrades a lint failure to an advisory (the file is already on disk). ruff is
a project dev dependency, so it is present whenever this suite runs.
"""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import post_ruff


def _ctx(path: Path) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=path,
        command=None,
        new_content=None,
        old_content=None,
    )


def test_should_advise_when_ruff_flags_the_written_file(tmp_path: Path) -> None:
    """An unused import (F401) makes ruff fail, which becomes an advisory."""
    f = tmp_path / "bad.py"
    f.write_text("import os\n")
    decision = post_ruff.check(_ctx(f))
    assert decision.severity == "advisory"


def test_should_allow_a_clean_file(tmp_path: Path) -> None:
    """A file ruff has no complaint about passes with no advisory."""
    f = tmp_path / "ok.py"
    f.write_text("x = 1\n")
    assert post_ruff.check(_ctx(f)).severity == "allow"


def test_should_ignore_non_python_files(tmp_path: Path) -> None:
    """Only Python files are linted."""
    f = tmp_path / "note.md"
    f.write_text("nothing here\n")
    assert post_ruff.check(_ctx(f)).severity == "allow"
