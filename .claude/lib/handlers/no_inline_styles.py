"""Block inline style escapes in .svelte files.

Catches all known evasions:
  • ``style="..."`` and ``style={...}`` (literal attribute, quoted or unquoted)
  • ``bind:style={...}`` (Svelte directive; sneaks past naive regex)
  • ``el.style.color = ...`` and ``el.style.cssText = ...`` in script blocks

Allowed escape hatch: ``style:--token-name={value}`` (Svelte's CSS-custom-
property bind) — that routes through the token system.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision

HANDLER = "no_inline_styles"
RULE_ID = "DS-002"
DOC = "docs/design-system.md#hard-rules"

# Attribute form. Matches both quoted and unquoted values, and the bind: variant.
# NOT matched: `style:foo={...}` (custom-property bind — the allowed escape hatch).
_ATTRIBUTE = re.compile(
    r"""
    (?:^|[\s'"({\[])                  # start-of-string or boundary char
    (?:bind:)?style                   # `style` or `bind:style`
    \s*=\s*                           # =
    (?:                               # value:
        "[^"]*"                       #   "..."
      | '[^']*'                       #   '...'
      | \{[^}]*\}                     #   {...}
      | [^\s>'"]+                     #   unquoted token (style=color:red)
    )
    """,
    re.VERBOSE,
)

# DOM API in script blocks: el.style.color = ..., el.style.cssText = ...
# This catches assignment to anything under `.style.`, but exempts reads.
_DOM_STYLE_WRITE = re.compile(r"\.style(?:\.\w+|\.cssText)\s*=")


def check(ctx: HookContext) -> Decision:
    """Return a deny if any inline-style escape is present."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "svelte":
        return Decision.allow(HANDLER)

    content = ctx.new_content
    attribute_hits: list[str] = _ATTRIBUTE.findall(content)
    dom_hits: list[str] = _DOM_STYLE_WRITE.findall(content)
    total = len(attribute_hits) + len(dom_hits)
    if total == 0:
        return Decision.allow(HANDLER)

    why_parts: list[str] = []
    if attribute_hits:
        why_parts.append(f"{len(attribute_hits)} inline style attribute(s)")
    if dom_hits:
        why_parts.append(f"{len(dom_hits)} `.style.X = ...` DOM assignment(s)")

    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why="Found " + " and ".join(why_parts) + ". Inline styles bypass the design system.",
        fix=(
            "Use Tailwind utilities (text-accent, p-4) or, for dynamic values, "
            "Svelte's `style:--token-name={value}` directive which routes through "
            "tokens. Mutate classes (`el.classList.toggle(...)`), not `.style`."
        ),
        doc=DOC,
    )
