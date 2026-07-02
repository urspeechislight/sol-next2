"""Pipeline config loader: config/sol.yaml -> frozen Config.

One YAML file, loaded, validated, and frozen in this one module: the typed
``Thresholds``/``Config`` dataclasses, the loader, and the structural
validators (required sections, pattern/behavior cross-references, atomicizer
rules, service keys, toc_sections, narrator_extraction) that used to live in
a separate ``_config_validate`` shard split off only for the old file-size
cap. Ported from sol-next's src/utils/config.py; the service-backed loaders
(ruvector, gazetteer, quran, ner) are omitted because those services are
disabled in the ported config, and the config carries only the sections the
ported phases actually read. Pattern compilation goes through
backend.patterns (CENTRAL-002), so this module imports no regex machinery
directly.

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

from backend.core.settings import get_settings
from backend.patterns import CompiledPattern, compile_pattern_table
from backend.pipeline.errors import ConfigError


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
        _validate_config(raw_dict, config_path)
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
        raw=raw_dict,
        compiled_patterns=compiled_patterns,
    )


def _validate_config(raw: dict[str, Any], path: Path) -> None:
    """Validate the whole config structure, raising ValueError on the first failure."""
    for key in ("patterns", "behaviors", "atomicizers", "extractors", "thresholds"):
        if key not in raw:
            raise ValueError(f"config/{path.name} missing required section: '{key}'")

    pattern_ids = {p["id"] for p in raw["patterns"]}
    for behavior in raw["behaviors"]:
        _validate_behavior_pattern_refs(behavior, pattern_ids)

    behavior_ids = {b["id"] for b in raw["behaviors"]}
    for behavior_id in raw["extractors"]:
        if behavior_id not in behavior_ids:
            raise ValueError(f"Extractor config references unknown behavior '{behavior_id}'")

    extractor_lists = list(raw["extractors"].values())
    has_narrator = any("narrator_extractor" in el for el in extractor_lists)

    _validate_atomicizer_rules(raw["atomicizers"], behavior_ids)
    for behavior in raw["behaviors"]:
        gate = behavior.get("genre_gate")
        if gate is not None and not isinstance(gate, list):
            raise ValueError(f"Behavior '{behavior['id']}' genre_gate must be a list")

    _validate_narrator_extraction(raw, has_narrator)
    _validate_toc_sections(raw)


def _validate_behavior_pattern_refs(behavior: dict[str, Any], pattern_ids: set[Any]) -> None:
    """Raise ValueError if any requires/any_of/none_of ref is an unknown pattern id."""
    for field_name in ("requires", "any_of", "none_of"):
        for ref in behavior.get(field_name, []):
            if ref not in pattern_ids:
                raise ValueError(
                    f"Behavior '{behavior['id']}' {field_name} references unknown pattern '{ref}'"
                )


def _validate_atomicizer_rules(atomicizers: dict[str, Any], behavior_ids: set[Any]) -> None:
    """Validate atomicizer rules reference known behaviors and valid strategies."""
    valid_strategies = {"whole_span", "sanad_matn_split"}
    for behavior_id, rule in atomicizers.items():
        if behavior_id.startswith("_"):
            continue
        if behavior_id not in behavior_ids:
            raise ValueError(f"Atomicizer config references unknown behavior '{behavior_id}'")
        strategy = rule.get("strategy")
        if strategy not in valid_strategies:
            raise ValueError(
                f"Atomicizer '{behavior_id}' has unknown strategy '{strategy}'. "
                f"Valid: {sorted(valid_strategies)}"
            )
        if strategy == "whole_span" and "unit_type" not in rule:
            raise ValueError(f"Atomicizer '{behavior_id}' uses whole_span but missing 'unit_type'")
        if strategy == "sanad_matn_split":
            for required_key in ("unit_types", "fallback_unit_type"):
                if required_key not in rule:
                    raise ValueError(
                        f"Atomicizer '{behavior_id}' uses sanad_matn_split "
                        f"but missing '{required_key}'"
                    )


def _validate_narrator_extraction(raw: dict[str, Any], has_narrator_extractor: bool) -> None:
    """Validate the narrator_extraction section.

    Required in full when narrator_extractor is in an extractor list; the
    three core keys are still required when the section is present otherwise.
    """
    narrator_cfg = raw.get("narrator_extraction")
    if has_narrator_extractor:
        if narrator_cfg is None:
            raise ValueError(
                "narrator_extraction section is required because narrator_extractor "
                "is in an extractor list"
            )
        for required_key in (
            "relative_references",
            "prepositional_an_exclusions",
            "narrative_context_words",
            "name_content_boundaries",
            "sentence_start_disqualifiers",
        ):
            if required_key not in narrator_cfg:
                raise ValueError(
                    f"narrator_extraction section is missing required key '{required_key}'"
                )
    elif narrator_cfg is not None:
        for required_key in (
            "relative_references",
            "prepositional_an_exclusions",
            "narrative_context_words",
        ):
            if required_key not in narrator_cfg:
                raise ValueError(
                    f"narrator_extraction section is present but '{required_key}' is missing"
                )


def _validate_toc_sections(raw: dict[str, Any]) -> None:
    """Validate toc_sections.content_start_patterns reference existing pattern ids."""
    toc_cfg = raw.get("toc_sections")
    if toc_cfg is None:
        return
    patterns = toc_cfg.get("content_start_patterns")
    if patterns is None:
        raise ValueError("toc_sections is present but missing 'content_start_patterns'")
    if not isinstance(patterns, list) or not patterns:
        raise ValueError("toc_sections.content_start_patterns must be a non-empty list")
    pattern_ids = {p["id"] for p in raw["patterns"]}
    for pat_id in cast(list[Any], patterns):
        if pat_id not in pattern_ids:
            raise ValueError(
                f"toc_sections.content_start_patterns references unknown pattern '{pat_id}'"
            )
