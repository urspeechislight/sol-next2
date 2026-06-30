"""Block inline style escapes in React/JSX (.tsx, .jsx) files.

Catches the inline-style patterns the design system forbids:
  • ``style="..."`` (string style prop)
  • a hardcoded object literal such as ``style={{ color: 'red' }}``
  • ``el.style.color = ...`` and ``el.style.cssText = ...`` in component code

The sanctioned escape hatch is setting a CSS custom property dynamically:
``style={{ '--token': value }}``, or through a variable or helper such as
``style={cssVar('--token', t)}``. That feeds the token system instead of
bypassing it, so a single-brace ``style={expr}`` and a ``--``-keyed object
literal are both allowed. A spaced ``const style = {...}`` variable is not a
match either, since Prettier keeps a real JSX prop tight against ``=``.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision

HANDLER = "no_inline_styles"
RULE_ID = "DS-002"
DOC = "docs/design-system.md#hard-rules"

# JSX inline-style prop, `style` tight against `=` (Prettier keeps it so).
# Flag a string style and a hardcoded object literal `style={{ color: ... }}`,
# but allow the CSS-custom-property escape hatch: the lookahead lets a `{{`
# whose first key is a quoted-or-backticked `--name` through, and a single
# brace `style={expr}` (a variable or a cssVar() helper) is not matched.
_ATTRIBUTE = re.compile(r"""(?:^|[\s'"({\[])style=(?:"[^"]*"|'[^']*'|\{\{(?!\s*['"\x60]?--))""")

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
            "or a className. For a dynamic value set a CSS custom property, "
            "style={{ '--token': value }} or the cssVar() helper. Toggle classes "
            "(`el.classList.toggle(...)`), never `.style`."
        ),
        doc=DOC,
    )
