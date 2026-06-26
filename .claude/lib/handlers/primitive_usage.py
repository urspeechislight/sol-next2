"""Force routes/feature code to use design-system primitives, not raw HTML.

Why: rendering a raw ``<button>`` in a route guarantees the component will
drift from the rest of the app's button styling. Primitives encapsulate the
full styling contract (sizing, focus ring, hover, disabled). Raw elements
inside design-system files are fine — that's where the primitives live.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision
from ..paths import is_design_system_file, is_in_frontend

HANDLER = "primitive_usage"
RULE_ID = "DS-003"
DOC = "docs/design-system.md#hard-rules"

# Tag names that must be the design-system primitive instead.
_BANNED_TAGS = {"button", "input", "textarea", "select"}
_TAG_PATTERN = re.compile(r"<(button|input|textarea|select)(\s|>|/)")
# `<svelte:element this="button">` is the same end-result as `<button>`.
_SVELTE_ELEMENT = re.compile(
    r"""<svelte:element\s+this\s*=\s*['"](button|input|textarea|select)['"]"""
)


def check(ctx: HookContext) -> Decision:
    """Return a deny if banned raw tags appear in a route/feature .svelte file."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "svelte":
        return Decision.allow(HANDLER)
    # Design-system itself can use raw tags — that's the implementation layer.
    if is_design_system_file(ctx.file_path):
        return Decision.allow(HANDLER)
    # Only enforce inside the frontend.
    if not is_in_frontend(ctx.file_path):
        return Decision.allow(HANDLER)

    found = sorted(
        {m.group(1) for m in _TAG_PATTERN.finditer(ctx.new_content)}
        | {m.group(1) for m in _SVELTE_ELEMENT.finditer(ctx.new_content)}
    )
    if not found:
        return Decision.allow(HANDLER)
    pretty = ", ".join(f"<{t}>" for t in found)

    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why=(
            f"Raw {pretty} element(s) found in a route/feature component. Routes "
            "must use design-system primitives so styling stays consistent."
        ),
        fix=(
            "Import from $lib/design-system: Button, Input, etc. If you need a new "
            "primitive, add it to lib/design-system/primitives/ first."
        ),
        doc=DOC,
    )
