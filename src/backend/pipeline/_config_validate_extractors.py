"""Extractor- and methodology-specific config validators.

Ported from sol-next's src/utils/config.py. Each guard checks the config
section a specific extractor family depends on, and only fires when that family
is referenced from the ``extractors:`` table. All raise ValueError naming the
broken reference; the config loader converts that to ConfigError.
"""

from __future__ import annotations

from typing import Any

from backend.core.constants import HADITH__MAX_NARRATOR_RANK

_KNOWN_SHIA_GRADES: frozenset[str] = frozenset(
    {
        "SAHIH_LI_DHATIHI",
        "SAHIH_LI_GHAYRIHI",
        "HASAN_LI_DHATIHI",
        "HASAN_LI_GHAYRIHI",
        "MUWATHTHAQ",
        "QAWI",
        "DA'IF",
        "DA'IF_JIDDAN",
        "MAWDU",
    }
)


def validate_narrator_extraction(raw: dict[str, Any], has_narrator_extractor: bool) -> None:
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


def validate_biography_extraction(raw: dict[str, Any], has_person_extractor: bool) -> None:
    """Validate the biography_extraction section, required when person_extractor is used."""
    bio_cfg = raw.get("biography_extraction")
    if has_person_extractor:
        if bio_cfg is None:
            raise ValueError(
                "biography_extraction section is required because person_extractor "
                "is in an extractor list"
            )
        if "name_boundaries" not in bio_cfg:
            raise ValueError(
                "biography_extraction section is missing required key 'name_boundaries'"
            )


def validate_rijal_extraction(raw: dict[str, Any], has_rijal_extractor: bool) -> None:
    """Validate the rijal_extraction section, required when rijal_entry_extractor is used."""
    rijal_cfg = raw.get("rijal_extraction")
    if has_rijal_extractor:
        if rijal_cfg is None:
            raise ValueError(
                "rijal_extraction section is required because rijal_entry_extractor "
                "is in an extractor list"
            )
        for required_key in ("name_delimiters", "death_date_trail", "kunya_start"):
            if required_key not in rijal_cfg:
                raise ValueError(
                    f"rijal_extraction section is missing required key '{required_key}'"
                )


def validate_name_decomposition(raw: dict[str, Any], has_person_extractor: bool) -> None:
    """Validate name_decomposition, required when any person-name extractor is in use."""
    nd_cfg = raw.get("name_decomposition")
    if has_person_extractor:
        if nd_cfg is None:
            raise ValueError(
                "name_decomposition section is required because a person-name "
                "extractor (person_extractor or rijal_entry_extractor) is in an extractor list"
            )
        for required_key in ("kunya_pattern", "laqab_boundaries"):
            if required_key not in nd_cfg:
                raise ValueError(
                    f"name_decomposition section is missing required key '{required_key}'"
                )


def validate_theme_taxonomy(raw: dict[str, Any], has_theme_extractor: bool) -> None:
    """Validate theme_taxonomy, required when theme_extractor is used."""
    taxonomy = raw.get("theme_taxonomy")
    if not has_theme_extractor:
        return
    if taxonomy is None:
        raise ValueError(
            "theme_taxonomy section is required because theme_extractor is in an extractor list"
        )
    if "classification_order" not in taxonomy:
        raise ValueError("theme_taxonomy section is missing required key 'classification_order'")
    if "domains" not in taxonomy:
        raise ValueError("theme_taxonomy section is missing required key 'domains'")

    domain_keys = set(taxonomy["domains"].keys())
    for order_key in taxonomy["classification_order"]:
        if order_key not in domain_keys:
            raise ValueError(
                f"theme_taxonomy.classification_order references unknown domain '{order_key}'"
            )
    for domain_key, domain in taxonomy["domains"].items():
        if "categories" not in domain:
            raise ValueError(f"theme_taxonomy.domains.{domain_key} is missing 'categories'")
        _validate_theme_categories(domain_key, domain["categories"])


def _validate_theme_categories(domain_key: str, categories: list[dict[str, Any]]) -> None:
    """Validate each theme category has id, label_ar, and keywords."""
    required_keys = {"id", "label_ar", "keywords"}
    for cat in categories:
        missing = required_keys - set(cat.keys())
        if missing:
            raise ValueError(
                f"theme_taxonomy.domains.{domain_key} category "
                f"is missing required keys: {sorted(missing)}"
            )


def validate_jarh_tadil_grades(raw: dict[str, Any]) -> None:
    """Validate jarh_tadil_grades has sunni and shia term-to-rank mappings."""
    jtg = raw.get("jarh_tadil_grades")
    if jtg is None:
        return
    if not isinstance(jtg, dict):
        raise TypeError("jarh_tadil_grades must be a mapping")
    for tradition in ("sunni", "shia"):
        if tradition not in jtg:
            raise ValueError(f"jarh_tadil_grades missing required tradition sub-key: '{tradition}'")
        if not isinstance(jtg[tradition], dict):
            raise TypeError(f"jarh_tadil_grades.{tradition} must be a mapping of term -> rank")


def validate_hadith_methodology_section(raw: dict[str, Any]) -> None:
    """Validate hadith_methodology: unique defect ids, grade hierarchy, valid ranks."""
    hm = raw["hadith_methodology"]
    _validate_chain_defect_ids(hm.get("chain_defect_types", []))
    grade_hierarchy = hm.get("grade_hierarchy")
    if not grade_hierarchy:
        raise ValueError("hadith_methodology.grade_hierarchy is required")
    grade_set = set(grade_hierarchy)
    _validate_sunni_methodology(hm.get("sunni", {}), grade_set)
    _validate_shia_methodology(hm.get("shia", {}))


def _validate_chain_defect_ids(defect_types: list[dict[str, Any]]) -> None:
    """Ensure all chain_defect_types have unique ids."""
    seen: set[str] = set()
    for defect in defect_types:
        did = defect["id"]
        if did in seen:
            raise ValueError(f"hadith_methodology.chain_defect_types has duplicate id: '{did}'")
        seen.add(did)


def _validate_sunni_methodology(sunni: dict[str, Any], grade_set: set[str]) -> None:
    """Validate sunni narrator_rank_to_grade and taqwiyah rank ranges."""
    allowed_grades = grade_set | {"HASAN_CONDITIONAL"}
    rank_to_grade = sunni.get("narrator_rank_to_grade", {})
    for rank, grade in rank_to_grade.items():
        if grade not in allowed_grades:
            raise ValueError(
                f"hadith_methodology.sunni.narrator_rank_to_grade rank {rank} "
                f"maps to unknown grade '{grade}'"
            )
    max_rank = max(rank_to_grade.keys()) if rank_to_grade else HADITH__MAX_NARRATOR_RANK
    for rank in sunni.get("taqwiyah_eligible_ranks", []):
        if not isinstance(rank, int) or rank < 1 or rank > max_rank:
            raise ValueError(
                f"hadith_methodology.sunni.taqwiyah_eligible_ranks has invalid rank: {rank}"
            )
    for rank in sunni.get("taqwiyah_blocked_ranks", []):
        if not isinstance(rank, int) or rank < 1 or rank > max_rank:
            raise ValueError(
                f"hadith_methodology.sunni.taqwiyah_blocked_ranks has invalid rank: {rank}"
            )


def _validate_shia_methodology(shia: dict[str, Any]) -> None:
    """Validate shia narrator_category_rules and narrator_rank_to_grade."""
    for rule_name, rule in shia.get("narrator_category_rules", {}).items():
        if not isinstance(rule, dict):
            raise TypeError(
                f"hadith_methodology.shia.narrator_category_rules.{rule_name} must be a mapping"
            )
    rank_to_grade = shia.get("narrator_rank_to_grade", {})
    for rank, grade in rank_to_grade.items():
        if grade not in _KNOWN_SHIA_GRADES:
            raise ValueError(
                f"hadith_methodology.shia.narrator_rank_to_grade rank {rank} "
                f"maps to unknown grade '{grade}'"
            )
