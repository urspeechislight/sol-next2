"""Audit reads of sensitive files; block reads of obvious secret stores.

The agent has many legitimate reasons to call Read/Grep/Glob, so this
handler is mostly advisory. We block reads of known secret stores (``.env``,
``.env.*``, ``id_rsa``, etc.) so the model can't accidentally surface
credentials into its context window.

Files outside the repo (``/etc/passwd``, ``/proc/self/environ``, ``~/.ssh``)
are also blocked.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from ..context import HookContext
from ..decision import Decision
from ..paths import REPO_ROOT

HANDLER = "sensitive_read"
RULE_ID = "SEC-002"
DOC = "docs/quality-standards.md#security"

_FORBIDDEN_NAMES = re.compile(
    r"(?:^|/)(?:\.env(?:\..+)?|id_rsa|id_ed25519|id_dsa|"
    r"\.netrc|\.pgpass|credentials\.json|service-account\.json)$"
)
_FORBIDDEN_DIRS = (
    "/etc/",
    "/proc/",
    "/sys/",
    "/root/",
    "/.ssh/",
    "/.aws/",
    "/.config/gcloud/",
)


def check(ctx: HookContext) -> Decision:
    """Block reads of known secret stores or out-of-repo system paths."""
    target = _extract_path(ctx)
    if target is None:
        return Decision.allow(HANDLER)

    posix = target.as_posix()

    if _FORBIDDEN_NAMES.search(posix):
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why=f"Read of likely-secret file: {posix}",
            fix=(
                "Don't read credentials into context. Reference them by name "
                "from your secret store / env-var loader instead."
            ),
            doc=DOC,
        )

    for forbidden in _FORBIDDEN_DIRS:
        if forbidden in posix:
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=f"Read of out-of-repo system path: {posix}",
                fix=(
                    "System paths are outside the project boundary. If you really "
                    "need them, run a scoped Bash command yourself."
                ),
                doc=DOC,
            )

    # Reads inside the repo are advisory only.
    try:
        target.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return Decision.advise(
            handler=HANDLER,
            rule_id="SEC-003",
            why=f"Read of path outside the repo: {posix}",
            fix="Confirm this is intentional.",
            doc=DOC,
        )
    return Decision.allow(HANDLER)


def _extract_path(ctx: HookContext) -> Path | None:
    """Pull a file_path-like string from the tool input regardless of tool name."""
    if ctx.file_path is not None:
        return ctx.file_path
    tool_input = ctx.raw.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return None
    for key in ("file_path", "path", "pattern"):
        value = tool_input.get(key)  # type: ignore[misc]
        if isinstance(value, str) and value:
            return Path(value)
    return None
