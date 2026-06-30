"""Tests for the SessionStart symbol-inventory builder."""

from __future__ import annotations

from pathlib import Path

import pytest

from lib import inventory, paths


def _make_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an empty repo with src/backend/ and point the builder at it."""
    repo = tmp_path / "repo"
    (repo / "src" / "backend").mkdir(parents=True)
    monkeypatch.setattr(inventory, "REPO_ROOT", repo)
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    return repo


def test_should_list_public_functions_and_classes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Public defs/classes are listed by file; private names are omitted."""
    repo = _make_repo(tmp_path, monkeypatch)
    (repo / "src/backend/text.py").write_text(
        "def normalize(s):\n    return s\n\n\nclass Reader:\n    pass\n\n\ndef _hidden():\n    return 1\n"
    )
    out = inventory.build_symbol_inventory()
    assert "def normalize" in out
    assert "class Reader" in out
    assert "_hidden" not in out
    assert "src/backend/text.py" in out


def test_should_skip_init_and_conftest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """__init__.py and conftest.py are excluded from the inventory."""
    repo = _make_repo(tmp_path, monkeypatch)
    (repo / "src/backend/__init__.py").write_text("def packaged():\n    return 1\n")
    (repo / "src/backend/conftest.py").write_text("def fixturish():\n    return 1\n")
    out = inventory.build_symbol_inventory()
    assert "packaged" not in out
    assert "fixturish" not in out


def test_should_report_empty_when_no_symbols(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty src/ yields the explicit no-symbols message, not a blank string."""
    _make_repo(tmp_path, monkeypatch)
    assert "no public symbols" in inventory.build_symbol_inventory()


def test_should_note_unparseable_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A broken file is surfaced as a parse note, never silently dropped."""
    repo = _make_repo(tmp_path, monkeypatch)
    (repo / "src/backend/ok.py").write_text("def good():\n    return 1\n")
    (repo / "src/backend/broken.py").write_text("def oops(:\n")
    out = inventory.build_symbol_inventory()
    assert "def good" in out
    assert "could not parse" in out
    assert "broken.py" in out
