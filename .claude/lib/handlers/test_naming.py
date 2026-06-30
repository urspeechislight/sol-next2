"""Enforce test naming convention: ``test_should_<verb>_<object>_<condition>``.

Why: descriptive test names form a readable spec when the test file is
scanned. Generic names like ``test_foo_works`` lose information.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision
from ..paths import is_in

HANDLER = "test_naming"
RULE_ID = "TEST-001"
DOC = "docs/quality-standards.md#tests"

_PY_TEST = re.compile(r"^def\s+(test_\w+)\s*\(", re.MULTILINE)
_TS_TEST = re.compile(r"\b(?:test|it)\s*\(\s*['\"]([^'\"]+)['\"]")
_GOOD_PY = re.compile(r"^test_should_[a-z][a-z0-9]+(?:_[a-z0-9]+){2,}$")
# TS/JS tests should *start* with "should" and have a real predicate after.
# Accept all common Vitest/Jest styles:
#   • snake_case:   "should_render_button_when_loading"
#   • camelCase:    "shouldRenderButtonWhenLoading"
#   • sentence:     "should render button when loading"
# Reject:
#   • "should"           — no predicate
#   • "shoulda"          — typo (no separator after "should")
#   • "renders correctly"— no "should" prefix
_GOOD_TS = re.compile(r"^should(?:[\s_][a-z0-9].*|[A-Z][A-Za-z0-9].*)$")


def check(ctx: HookContext) -> Decision:
    """Return a deny if a test name doesn't match the naming convention."""
    if not ctx.is_write or ctx.new_content is None or ctx.file_path is None:
        return Decision.allow(HANDLER)

    # File counts as a test file only if:
    #  • it lives under a `tests` dir, OR
    #  • its stem starts with `test_` / ends with `.test` / `.spec`
    # `contest_helpers.py`, `attestation.py`, etc. no longer false-match.
    stem = ctx.file_path.stem.lower()
    is_test_file = (
        is_in(ctx.file_path, "tests")
        or stem.startswith("test_")
        or stem.endswith((".test", ".spec"))
    )
    if not is_test_file:
        return Decision.allow(HANDLER)

    if ctx.suffix == "py":
        bad = [n for n in _PY_TEST.findall(ctx.new_content) if not _GOOD_PY.match(n)]
        if bad:
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    "Python test name(s) don't follow "
                    f"`test_should_<verb>_<object>_<condition>`: {bad[0]}"
                ),
                fix="Rename to e.g. `test_should_return_404_when_user_not_found`.",
                doc=DOC,
            )
    elif ctx.suffix in {"ts", "tsx", "js", "jsx"}:
        bad = [n for n in _TS_TEST.findall(ctx.new_content) if not _GOOD_TS.match(n)]
        if bad:
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    f"TS test name(s) don't follow `should...` form: {bad[0]!r}. "
                    "Tests should read as a spec sentence."
                ),
                fix="Rename to e.g. `should_render_button_when_loading`.",
                doc=DOC,
            )
    return Decision.allow(HANDLER)
