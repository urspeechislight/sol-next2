"""Pipeline config loader: config/sol.yaml -> frozen Config.

One YAML file, loaded and validated once at startup, then passed frozen to
every phase. Ported from sol-next's src/utils/config.py with these sol-next2
adaptations: the service-backed loaders (ruvector, gazetteer, quran, ner) are
omitted because those services are disabled in the ported config (ruvector and
ner are substituted; gazetteer and quran are wired in later milestones), so
``narrator_gazetteer`` is empty and the quran index is dropped until the quran
service lands. Pattern compilation goes through backend.patterns (CENTRAL-002),
so this module imports no regex machinery directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from backend.core.errors import ConfigError
from backend.core.settings import get_settings
from backend.patterns import CompiledPattern, compile_pattern_table
from backend.pipeline._config_validate import validate_config


@dataclass(frozen=True)
class Config:
    """The complete runtime configuration for the ported pipeline.

    Loaded from config/sol.yaml at startup and frozen; every phase receives this
    object and no phase reads YAML directly. ``compiled_patterns`` is the
    ``(pattern_id, compiled_regex)`` table built once at load time.
    """

    patterns: list[dict[str, Any]]
    behaviors: list[dict[str, Any]]
    atomicizers: dict[str, Any]
    extractors: dict[str, list[str]]
    graph: dict[str, Any]
    thresholds: dict[str, float]
    services: dict[str, Any]
    narrator_gazetteer: frozenset[str]
    raw: dict[str, Any]
    compiled_patterns: tuple[tuple[str, CompiledPattern], ...]

    def threshold_int(self, name: str) -> int:
        """Return ``thresholds[name]`` as int; KeyError if absent (config is SSOT)."""
        return int(self.thresholds[name])

    def threshold_float(self, name: str) -> float:
        """Return ``thresholds[name]`` as float, for genuinely fractional thresholds."""
        return float(self.thresholds[name])


def load_config(path: Path | None = None) -> Config:
    """Load and validate config/sol.yaml, or raise ConfigError.

    Defaults to the ``pipeline_config`` path from settings. Never returns a
    partially-valid config: either the whole file validates and the pipeline can
    run, or it raises and the pipeline does not start.
    """
    config_path = path if path is not None else get_settings().pipeline_config
    if not config_path.exists():
        raise ConfigError(f"Pipeline config not found: {config_path}")
    try:
        with config_path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Pipeline config is not valid YAML: {config_path}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"Pipeline config root must be a mapping: {config_path}")

    try:
        validate_config(raw, config_path)
    except (ValueError, TypeError) as exc:
        raise ConfigError(str(exc)) from exc

    try:
        compiled_patterns = compile_pattern_table(raw["patterns"])
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc

    return Config(
        patterns=raw["patterns"],
        behaviors=raw["behaviors"],
        atomicizers=raw["atomicizers"],
        extractors=raw["extractors"],
        graph=raw["graph"],
        thresholds=raw["thresholds"],
        services=raw.get("services", {}),
        narrator_gazetteer=frozenset(),
        raw=raw,
        compiled_patterns=compiled_patterns,
    )
