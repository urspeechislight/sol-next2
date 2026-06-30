"""Cross-stack golden: the Arabic folds in ``backend.patterns`` must produce the
exact table in ``tests/fixtures/arabic_fold_golden.json``. The frontend asserts
the SAME table in ``frontend/src/lib/arabic.golden.test.ts``, so the two stacks
fold identically by construction rather than by two hand-kept copies drifting.
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.patterns import fold_search, normalize_arabic

_GOLDEN = json.loads(
    (Path(__file__).resolve().parent / "fixtures" / "arabic_fold_golden.json").read_text(
        encoding="utf-8"
    )
)


def test_should_match_golden_table_when_folding_for_search() -> None:
    """``fold_search`` reproduces every fold_search row of the shared table."""
    for case in _GOLDEN["fold_search"]:
        assert fold_search(case["in"]) == case["out"], case["in"]


def test_should_match_golden_table_when_normalizing_a_name() -> None:
    """``normalize_arabic`` reproduces every normalize_name row of the table."""
    for case in _GOLDEN["normalize_name"]:
        assert normalize_arabic(case["in"]) == case["out"], case["in"]
