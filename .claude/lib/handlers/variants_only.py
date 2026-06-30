"""Block ad-hoc status/variant maps in components.

Why: status -> palette / band -> status mappings are SSOT in
``lib/design-system/variants.ts``. Inline maps that duplicate the design
vocabulary fragment the system and make rebranding painful.

Heuristic: any object literal whose KEYS contain at least 3 of the canonical
status vocabulary {success, warning, danger, info, accent, muted, ok, warn,
bad, good, error, alert, neutral, primary, secondary} is flagged. Comments
and string contents are stripped before scanning so a comment like
``// info: missing`` doesn't trigger a false positive.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision
from ..paths import is_design_system_file

HANDLER = "variants_only"
RULE_ID = "DS-004"
# Variant maps must declare ≥ N status keys before being flagged as
# a status→palette map living outside variants.ts.
_MIN_STATUS_HITS = 3
DOC = "docs/design-system.md#hard-rules"

_STATUS_KEYS = {
    "success",
    "warning",
    "danger",
    "info",
    "accent",
    "muted",
    "ok",
    "warn",
    "bad",
    "good",
    "error",
    "alert",
    "neutral",
    "primary",
    "secondary",
}

_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_STRING_LITERAL = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'|`[^`]*`', re.DOTALL)
# Object key: `success:`, `'warning':`. Captures the bare key name.
_KEY = re.compile(r"(?:^|[\s,{])(?:['\"](\w+)['\"]|(\w+))\s*:")


def _strip_noise(content: str) -> str:
    """Remove comments and string contents to leave only structural code."""
    content = _BLOCK_COMMENT.sub("", content)
    content = _HTML_COMMENT.sub("", content)
    content = _LINE_COMMENT.sub("", content)
    return _STRING_LITERAL.sub('""', content)


def _max_status_hits(content: str) -> int:
    """Return the max count of distinct status-vocab keys in any object literal."""
    max_hits = 0
    depth = 0
    start = -1
    for i, ch in enumerate(content):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                block = content[start + 1 : i]
                keys = {m.group(1) or m.group(2) for m in _KEY.finditer(block)}
                hits = len(keys & _STATUS_KEYS)
                max_hits = max(max_hits, hits)
                start = -1
    return max_hits


def check(ctx: HookContext) -> Decision:
    """Return a deny if an object outside the design system uses ≥3 status keys."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)
    if ctx.suffix not in {"ts", "tsx", "js", "jsx"}:
        return Decision.allow(HANDLER)
    if is_design_system_file(ctx.file_path):
        return Decision.allow(HANDLER)

    cleaned = _strip_noise(ctx.new_content)
    hits = _max_status_hits(cleaned)
    if hits < _MIN_STATUS_HITS:
        return Decision.allow(HANDLER)

    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why=(
            f"An object literal with {hits} status-style keys was found. Variant "
            "maps live only in lib/design-system/variants.ts (SSOT)."
        ),
        fix=(
            "Move the map to variants.ts and import it. If the map needs to "
            "diverge from the canonical statuses, talk to design first."
        ),
        doc=DOC,
    )
