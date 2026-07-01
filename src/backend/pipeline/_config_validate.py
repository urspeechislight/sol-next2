"""Structural config validation and the validate_config orchestrator.

Ported from sol-next's src/utils/config.py _validate tree, then cut down to
the sections the ported phases actually read: required sections,
pattern/behavior cross-references, atomicizer rules, service keys,
toc_sections, and narrator_extraction. Threshold presence is enforced by the
typed ``Thresholds`` dataclass in ``config.py`` (one home, no drift), so no
separate required-thresholds list exists here. Raises ValueError naming the
broken reference on any failure; the config loader converts that to
ConfigError.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast


def validate_config(raw: dict[str, Any], path: Path) -> None:
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

    _validate_services(raw.get("services", {}))
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


def _validate_services(services: dict[str, Any]) -> None:
    """Validate each enabled service block carries its required keys."""
    ruvector_cfg = services.get("ruvector", {})
    if ruvector_cfg.get("enabled"):
        for required_key in ("url", "collection", "dimensions"):
            if required_key not in ruvector_cfg:
                raise ValueError(
                    f"services.ruvector.enabled is true but '{required_key}' is missing"
                )

    gaz_cfg = services.get("gazetteer", {})
    if gaz_cfg.get("enabled") and "narrator_path" not in gaz_cfg:
        raise ValueError("services.gazetteer.enabled is true but 'narrator_path' is missing")

    ner_cfg = services.get("ner", {})
    if ner_cfg.get("enabled"):
        for required_key in ("url", "timeout_seconds", "endpoint", "verify_ssl"):
            if required_key not in ner_cfg:
                raise ValueError(f"services.ner.enabled is true but '{required_key}' is missing")

    quran_cfg = services.get("quran", {})
    if quran_cfg.get("enabled") and "index_path" not in quran_cfg:
        raise ValueError("services.quran.enabled is true but 'index_path' is missing")


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
