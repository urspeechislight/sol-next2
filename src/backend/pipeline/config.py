"""Pipeline config loader: config/sol.yaml -> frozen Config.

One YAML file, loaded and validated once at startup, then passed frozen to
every phase. Ported from sol-next's src/utils/config.py with these sol-next2
adaptations: the service-backed loaders (ruvector, gazetteer, quran, ner) are
omitted because those services are disabled in the ported config, and the
config carries only the sections the ported phases actually read. Pattern
compilation goes through backend.patterns (CENTRAL-002), so this module
imports no regex machinery directly.

``Thresholds`` is a typed frozen dataclass rather than a string-keyed dict:
a misspelled threshold name is now a pyright error at the call site and a
loud ConfigError at load time, instead of a KeyError mid-build (or, worse,
a silent ``.get`` default).
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, cast

import yaml

from backend.core.errors import ConfigError
from backend.core.settings import get_settings
from backend.patterns import CompiledPattern, compile_pattern_table
from backend.pipeline._config_validate import validate_config


@dataclass(frozen=True)
class Thresholds:
    """Every numeric threshold a ported phase reads, one typed field each.

    Loaded from ``thresholds:`` in config/sol.yaml; the loader raises
    ConfigError naming any missing key. Adding a field here IS adding the
    requirement, so the validator and the consumer can never drift apart.
    """

    evidence_context_chars: int
    min_span_chars: int
    isnad_tail_max_chars: int
    isnad_merge_name_max_chars: int
    heading_split_min_heading_chars: int
    heading_split_max_heading_chars: int
    narrative_heading_max_chars: int
    question_verb_lookback_chars: int
    narrator_disqualifier_lookahead_chars: int
    narrator_narrative_lookahead_chars: int
    narrator_name_max_chars: int
    isnad_chain_proximity_max: int
    isnad_chain_gap_max: int


def _build_thresholds(raw_thresholds: dict[str, Any], path: Path) -> Thresholds:
    """Project the raw thresholds mapping into the typed dataclass, failing loud."""
    field_names = [f.name for f in fields(Thresholds)]
    missing = [name for name in field_names if name not in raw_thresholds]
    if missing:
        raise ConfigError(f"config/{path.name} thresholds missing: {sorted(missing)}")
    return Thresholds(**{name: int(raw_thresholds[name]) for name in field_names})


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
    thresholds: Thresholds
    services: dict[str, Any]
    raw: dict[str, Any]
    compiled_patterns: tuple[tuple[str, CompiledPattern], ...]


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
    raw_dict = cast(dict[str, Any], raw)

    try:
        validate_config(raw_dict, config_path)
    except (ValueError, TypeError) as exc:
        raise ConfigError(str(exc)) from exc

    try:
        compiled_patterns = compile_pattern_table(raw_dict["patterns"])
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc

    return Config(
        patterns=raw_dict["patterns"],
        behaviors=raw_dict["behaviors"],
        atomicizers=raw_dict["atomicizers"],
        extractors=raw_dict["extractors"],
        thresholds=_build_thresholds(raw_dict["thresholds"], config_path),
        services=raw_dict.get("services", {}),
        raw=raw_dict,
        compiled_patterns=compiled_patterns,
    )
