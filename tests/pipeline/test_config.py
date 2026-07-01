"""Tests for the ported pipeline config loader (config/sol.yaml -> Config)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.core.errors import ConfigError
from backend.pipeline.config import load_config


def test_should_load_config_when_sol_yaml_present() -> None:
    cfg = load_config()
    assert len(cfg.patterns) == len(cfg.compiled_patterns)
    assert "HADITH_TRANSMISSION" in {b["id"] for b in cfg.behaviors}
    assert cfg.threshold_int("evidence_context_chars") == 50


def test_should_raise_config_error_when_path_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path / "missing.yaml")
