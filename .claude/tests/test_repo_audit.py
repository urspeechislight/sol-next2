"""Tests for the whole-repo SSOT/DRY audit gate (lib/repo_audit).

Each check is exercised against a tiny synthetic repo to prove it CATCHES the
exact classes that slipped past the per-file harness, plus one test that the
live checkout is clean (the ratchet).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lib import repo_audit
from lib.repo_audit import (
    audit,
    check_canonical_modules,
    check_control_radius,
    check_dark_palette,
    check_no_raw_interactive,
    check_no_syspath,
    check_scope_frame,
    check_single_definitions,
    check_suppression_budget,
)

_LIVE_ROOT = Path(__file__).resolve().parent.parent.parent


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_should_flag_a_duplicate_canonical_module(tmp_path: Path) -> None:
    _write(tmp_path, "frontend/src/lib/routes.ts", "export const API = {};\n")
    _write(tmp_path, "frontend/src/lib/api/routes.ts", "export const API = {};\n")
    dup = next(v for v in check_canonical_modules(tmp_path) if "routes.ts" in v.why)
    assert dup.rule_id == "AUDIT-SSOT-001"
    assert len(dup.locations) == 2


def test_should_flag_a_capability_defined_twice(tmp_path: Path) -> None:
    _write(tmp_path, "src/backend/models/reader.py", 'HadithGrade = Literal["sahih"]\n')
    _write(tmp_path, "src/backend/models/daily.py", 'HadithGrade = Literal["sahih"]\n')
    flagged = check_single_definitions(tmp_path)
    assert any(v.rule_id == "AUDIT-SSOT-002" and "HadithGrade" in v.why for v in flagged)


def test_should_pass_when_capability_defined_once(tmp_path: Path) -> None:
    _write(tmp_path, "src/backend/models/grades.py", 'HadithGrade = Literal["sahih"]\n')
    assert not any("HadithGrade" in v.why for v in check_single_definitions(tmp_path))


def test_should_flag_a_repeated_suppression(tmp_path: Path) -> None:
    body = (
        "a = 1  # pyright: ignore[reportUnusedFunction]\n"
        "b = 1  # pyright: ignore[reportUnusedFunction]\n"
        "c = 1  # pyright: ignore[reportUnusedFunction]\n"
        "d = 1  # pyright: ignore[reportUnusedFunction]\n"
    )
    _write(tmp_path, "src/backend/x.py", body)
    flagged = check_suppression_budget(tmp_path)
    assert any(
        v.rule_id == "AUDIT-SUPPRESS-001" and "reportUnusedFunction" in v.why for v in flagged
    )


def test_should_flag_syspath_manipulation(tmp_path: Path) -> None:
    _write(tmp_path, "scripts/x.py", "import sys\nsys.path.insert(0, 'src')\n")
    assert any(v.rule_id == "AUDIT-IMPORT-001" for v in check_no_syspath(tmp_path))


def test_should_report_clean_when_no_violations(tmp_path: Path) -> None:
    _write(tmp_path, "scripts/x.py", "value = 1\n")
    assert check_no_syspath(tmp_path) == []
    assert check_suppression_budget(tmp_path) == []


def test_should_flag_a_raw_interactive_element_in_features(tmp_path: Path) -> None:
    src = "export const W = () => <button>go</button>;\n"
    _write(tmp_path, "frontend/src/features/x/Widget.tsx", src)
    flagged = check_no_raw_interactive(tmp_path)
    assert any(v.rule_id == "AUDIT-DS-001" and "Widget.tsx" in v.why for v in flagged)


def test_should_not_flag_design_system_components_in_features(tmp_path: Path) -> None:
    src = "export const W = () => <Button>go</Button>;\n"
    _write(tmp_path, "frontend/src/features/x/Widget.tsx", src)
    assert not any("Widget.tsx" in v.why for v in check_no_raw_interactive(tmp_path))


def test_should_flag_when_a_baselined_file_exceeds_its_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rel = "frontend/src/features/x/Legacy.tsx"
    monkeypatch.setattr(repo_audit, "_RAW_INTERACTIVE_BASELINE", {rel: 4})
    _write(tmp_path, rel, "export const R = () => <>" + "<button>x</button>" * 5 + "</>;\n")
    flagged = check_no_raw_interactive(tmp_path)
    assert any(v.rule_id == "AUDIT-DS-001" and "only 4 allowed" in v.why for v in flagged)


def test_should_allow_a_baselined_file_at_its_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rel = "frontend/src/features/x/Legacy.tsx"
    monkeypatch.setattr(repo_audit, "_RAW_INTERACTIVE_BASELINE", {rel: 4})
    _write(tmp_path, rel, "export const R = () => <>" + "<button>x</button>" * 4 + "</>;\n")
    assert not any("Legacy.tsx" in v.why for v in check_no_raw_interactive(tmp_path))


_PRIM = "frontend/src/lib/design-system/primitives"
_TOKENS = "frontend/src/lib/design-system/tokens.css"


def test_should_flag_a_control_primitive_using_radius_pill(tmp_path: Path) -> None:
    _write(tmp_path, f"{_PRIM}/Pill.css", ".ds-pill { border-radius: var(--radius-pill); }\n")
    flagged = check_control_radius(tmp_path)
    assert any(v.rule_id == "AUDIT-RADIUS-001" and "radius-pill" in v.why for v in flagged)


def test_should_flag_a_control_primitive_missing_radius_control(tmp_path: Path) -> None:
    _write(tmp_path, f"{_PRIM}/Button.css", ".ds-btn { border-radius: var(--radius-md); }\n")
    flagged = check_control_radius(tmp_path)
    assert any(v.rule_id == "AUDIT-RADIUS-001" and "does not reference" in v.why for v in flagged)


def test_should_pass_a_control_primitive_on_radius_control(tmp_path: Path) -> None:
    _write(tmp_path, f"{_PRIM}/Button.css", ".ds-btn { border-radius: var(--radius-control); }\n")
    assert check_control_radius(tmp_path) == []


def test_should_allow_spinner_to_stay_a_pill(tmp_path: Path) -> None:
    _write(tmp_path, f"{_PRIM}/Spinner.css", ".ds-spinner { border-radius: var(--radius-pill); }\n")
    assert check_control_radius(tmp_path) == []


def test_should_flag_a_dark_block_with_an_oklch_literal(tmp_path: Path) -> None:
    css = "[data-reader-theme='dark'] {\n  --color-reader-bg: oklch(0.16 0.008 250);\n}\n"
    _write(tmp_path, _TOKENS, css)
    assert any(v.rule_id == "AUDIT-THEME-001" for v in check_dark_palette(tmp_path))


def test_should_pass_dark_blocks_that_reference_the_palette(tmp_path: Path) -> None:
    css = (
        "[data-theme='dark'] {\n  --color-bg: var(--palette-night-900);\n"
        "  --color-scrim: rgba(0, 0, 0, 0.62);\n}\n"
        "[data-reader-theme='dark'] {\n  --color-reader-bg: var(--palette-night-900);\n"
        "  --m: color-mix(in oklch, var(--palette-amber-500) 38%, transparent);\n}\n"
    )
    _write(tmp_path, _TOKENS, css)
    assert check_dark_palette(tmp_path) == []


def test_should_flag_a_search_scope_without_results_frame(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "frontend/src/features/search/RogueScope.tsx",
        "export function X() { return searchBooks('q'); }\n",
    )
    flagged = check_scope_frame(tmp_path)
    assert any(v.rule_id == "AUDIT-SCOPE-001" and "RogueScope.tsx" in v.why for v in flagged)


def test_should_pass_a_search_scope_using_results_frame(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "frontend/src/features/search/GoodScope.tsx",
        "import { ResultsFrame } from './ResultsFrame';\n"
        "export function X() { return searchBooks('q'); }\n",
    )
    assert check_scope_frame(tmp_path) == []


def test_should_pass_a_scope_delegating_to_corpus_results(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "frontend/src/features/search/BindingScope.tsx",
        "import { CorpusResults } from './CorpusResults';\n"
        "export function X() { searchBooks('q'); return <CorpusResults />; }\n",
    )
    assert check_scope_frame(tmp_path) == []


def test_should_ignore_search_files_that_do_not_fetch(tmp_path: Path) -> None:
    _write(tmp_path, "frontend/src/features/search/SearchFilters.tsx", "export const F = 1;\n")
    assert check_scope_frame(tmp_path) == []


def test_should_keep_the_live_repo_clean() -> None:
    assert audit(_LIVE_ROOT) == []
