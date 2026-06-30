"""Block raw color literals outside the token SSOT.

Why: design tokens (``tokens.css``) are the only place colors are defined.
Letting raw ``#abc`` / ``rgb(...)`` / ``hsl(...)`` / ``oklch(...)`` literals
into components defeats SSOT — themes can no longer be retuned in one place.

Comments are stripped before scanning so a TODO like ``// design wants
#ff00ff`` doesn't trigger a false positive. Strings are kept (a hex inside
a string IS a real value — e.g. someone returning ``"#abc"`` from a function).
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision
from ..paths import is_design_token_file

HANDLER = "no_raw_colors"
RULE_ID = "DS-001"
DOC = "docs/design-system.md#hard-rules"

_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
_FN = re.compile(r"\b(rgb|rgba|hsl|hsla|oklch|oklab|hwb|lab|lch)\s*\(")
_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_PYTHON_COMMENT = re.compile(r"^\s*#[^\n]*", re.MULTILINE)


def _strip_comments(content: str) -> str:
    """Drop comments before scanning — they may legitimately reference colors."""
    content = _BLOCK_COMMENT.sub("", content)
    content = _HTML_COMMENT.sub("", content)
    content = _LINE_COMMENT.sub("", content)
    return _PYTHON_COMMENT.sub("", content)


def check(ctx: HookContext) -> Decision:
    """Return a deny if raw color literals appear outside the SSOT files."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)
    if ctx.suffix not in {"svelte", "ts", "tsx", "js", "jsx", "css"}:
        return Decision.allow(HANDLER)
    if is_design_token_file(ctx.file_path):
        return Decision.allow(HANDLER)

    content = _strip_comments(ctx.new_content)
    hex_hits = [m.group(0) for m in _HEX.finditer(content)]
    fn_hits = [m.group(1) for m in _FN.finditer(content)]
    hits = hex_hits + fn_hits

    if not hits:
        return Decision.allow(HANDLER)

    sample = ", ".join(sorted(set(hits))[:5])
    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why=(
            f"Raw color literal(s) found: {sample}. Colors are SSOT and may only "
            "be defined in src/frontend/lib/design-system/tokens.css."
        ),
        fix=(
            "Replace with a token: a Tailwind utility (e.g. bg-accent, text-fg-2) "
            "or a CSS var (var(--color-accent)). To add a new color, edit tokens.css."
        ),
        doc=DOC,
    )
