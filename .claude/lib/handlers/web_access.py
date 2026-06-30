"""Log every external fetch; block known data-exfil-shaped destinations.

Most fetches are legitimate (docs, GitHub, package registries). The handler
adds an advisory-level audit trail for everything, and blocks fetches whose
URL matches any pattern in the deny-list (currently empty by default — extend
in policies as you discover hostile destinations).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from urllib.parse import urlparse

from ..context import HookContext
from ..decision import Decision

HANDLER = "web_access"
RULE_ID = "SEC-004"
DOC = "docs/quality-standards.md#security"

# Hostnames or URL substrings to block outright. Extend in your fork.
_DENY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|169\.254\."),
    re.compile(r"://[^/]*\.local(?:/|$)"),
    re.compile(r"://[^/]*\.internal(?:/|$)"),
)


def check(ctx: HookContext) -> Decision:
    """Block deny-listed hosts; advisory for everything else."""
    tool_input = ctx.raw.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return Decision.allow(HANDLER)
    raw_url = tool_input.get("url") or tool_input.get("query")  # type: ignore[misc]
    if not isinstance(raw_url, str) or not raw_url:
        return Decision.allow(HANDLER)
    url: str = raw_url

    for pat in _DENY_PATTERNS:
        if pat.search(url):
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=f"Fetch to deny-listed host: {urlparse(url).netloc}",
                fix="External fetches must target public, non-internal URLs.",
                doc=DOC,
            )

    return Decision.advise(
        handler=HANDLER,
        rule_id="SEC-005",
        why=f"External fetch logged: {urlparse(url).netloc or url}",
        fix="No action needed — recorded in audit log.",
        doc=DOC,
    )
