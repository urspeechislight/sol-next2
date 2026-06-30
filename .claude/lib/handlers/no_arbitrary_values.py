"""Block Tailwind arbitrary values for spacing/sizing tokens.

Why: ``no_raw_colors`` already prevents ``bg-[#abc]``. But ``text-[14px]``,
``p-[7px]``, ``mt-[3rem]``, ``w-[200px]``, and friends bypass the spacing /
type-scale tokens. Letting them through fragments the design system the
same way raw colors would.

Allowed: arbitrary values that resolve to a token (``bg-[var(--color-x)]``,
``text-[length:var(--text-lg)]``). Block: numeric/unit literals.

The rule applies to all utility prefixes that have a token equivalent —
spacing, type scale, sizing, gap, inset, line-height, letter-spacing, etc.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision
from ..paths import is_design_token_file

HANDLER = "no_arbitrary_values"
RULE_ID = "DS-005"
DOC = "docs/design-system.md#hard-rules"

# Utility prefixes that have a token registry. Each `<prefix>-[value]` must
# either reference a CSS variable or a known token (like fr/auto/full).
_PREFIXES = (
    r"text|leading|tracking|"
    r"m[trblxy]?|p[trblxy]?|space-[xy]|gap|gap-[xy]|"
    r"w|h|min-w|min-h|max-w|max-h|"
    r"top|left|right|bottom|inset(?:-[xy])?|"
    r"rounded(?:-[trbl]{1,2})?|"
    r"shadow|"
    r"font|"
    r"opacity|"
    r"duration|delay"
)
_ARBITRARY = re.compile(rf"\b(?:{_PREFIXES})-\[([^\]]+)\]")
_ALLOWED_VALUE = re.compile(
    r"^(?:var\(--[\w-]+\)|length:var\(--[\w-]+\)|[\w-]+:var\(--[\w-]+\)|fr|auto|full|min|max|fit-content|0)$"
)


def check(ctx: HookContext) -> Decision:
    """Return a deny if a Tailwind arbitrary value uses a raw size literal."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)
    if ctx.suffix not in {"svelte", "ts", "tsx", "js", "jsx", "css"}:
        return Decision.allow(HANDLER)
    if is_design_token_file(ctx.file_path):
        return Decision.allow(HANDLER)

    bad: list[str] = []
    for match in _ARBITRARY.finditer(ctx.new_content):
        value = match.group(1).strip()
        if not _ALLOWED_VALUE.match(value):
            bad.append(match.group(0))
    if not bad:
        return Decision.allow(HANDLER)

    sample = ", ".join(bad[:3])
    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why=(
            f"Tailwind arbitrary value(s) with raw literals: {sample}. "
            "Spacing, sizes, type-scale, and motion are SSOT — use a token-backed "
            "utility (`text-lg`, `p-4`, `rounded-md`) or `var(--token-name)` arbitrary."
        ),
        fix=(
            "Replace with a token utility (`text-lg`), or add a token to "
            "tokens.css and reference it as `text-[length:var(--text-foo)]`."
        ),
        doc=DOC,
    )
