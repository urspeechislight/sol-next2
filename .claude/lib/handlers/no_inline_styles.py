"""Block inline style escapes in React/JSX (.tsx, .jsx) files.

Catches the inline-style patterns the design system forbids:
  • ``style={{ ... }}`` and ``style={expr}`` (the JSX inline-style prop)
  • ``style="..."`` (string style prop)
  • ``el.style.color = ...`` and ``el.style.cssText = ...`` in component code

The JSX attribute forms are matched only when ``style`` is written tight
against ``=`` (``style={`` / ``style="``), which is how Prettier formats a
JSX prop; a spaced ``const style = {...}`` variable is deliberately not a
match.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision

HANDLER = "no_inline_styles"
RULE_ID = "DS-002"
DOC = "docs/design-system.md#hard-rules"

# JSX inline-style prop: `style` tight against `=` (no spaces, as Prettier
# formats a JSX attribute), then `{` (object/expr) or a quote. A spaced
# `style = {...}` variable declaration is intentionally not matched.
_ATTRIBUTE = re.compile(r"""(?:^|[\s'"({\[])style=(?:"[^"]*"|'[^']*'|\{)""")

# DOM API in component code: el.style.color = ..., el.style.cssText = ...
_DOM_STYLE_WRITE = re.compile(r"\.style(?:\.\w+|\.cssText)\s*=")


def check(ctx: HookContext) -> Decision:
    """Return a deny if any inline-style escape is present."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix not in {"tsx", "jsx"}:
        return Decision.allow(HANDLER)

    content = ctx.new_content
    attribute_hits: list[str] = _ATTRIBUTE.findall(content)
    dom_hits: list[str] = _DOM_STYLE_WRITE.findall(content)
    total = len(attribute_hits) + len(dom_hits)
    if total == 0:
        return Decision.allow(HANDLER)

    why_parts: list[str] = []
    if attribute_hits:
        why_parts.append(f"{len(attribute_hits)} inline style prop(s)")
    if dom_hits:
        why_parts.append(f"{len(dom_hits)} `.style.X = ...` DOM assignment(s)")

    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why="Found " + " and ".join(why_parts) + ". Inline styles bypass the design system.",
        fix=(
            "Use design-system tokens through Tailwind utilities (text-accent, p-4) "
            "or a className. Toggle classes (`el.classList.toggle(...)`), never `.style`."
        ),
        doc=DOC,
    )
