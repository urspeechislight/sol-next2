"""Tests for the Python version guard in _bootstrap.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_HOOKS = Path(__file__).resolve().parent.parent / "hooks"


def _load_bootstrap():
    """Import _bootstrap fresh — once per test, to evaluate guard at call time."""
    spec = importlib.util.spec_from_file_location("_bootstrap_test", _HOOKS / "_bootstrap.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_should_define_minimum_python_version() -> None:
    """`MIN_PYTHON` constant exists and targets 3.10+."""
    mod = _load_bootstrap()
    assert mod.MIN_PYTHON >= (3, 10)


def test_should_pass_when_python_meets_minimum() -> None:
    """Running on a supported Python — module loads without exit."""
    mod = _load_bootstrap()
    # If we got here, the version guard didn't sys.exit.
    assert sys.version_info[:2] >= mod.MIN_PYTHON


def test_should_exit_when_python_below_minimum(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Simulated old Python — guard exits with code 2."""
    mod = _load_bootstrap()
    monkeypatch.setattr(sys, "version_info", (3, 9, 0, "final", 0))
    with pytest.raises(SystemExit) as exc:
        mod._enforce_python_version()
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "Python 3.10+" in captured.err
