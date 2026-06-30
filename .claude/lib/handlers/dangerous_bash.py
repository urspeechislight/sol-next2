"""PreToolUse:Bash — block obviously dangerous shell commands.

This is a coarse safety net: it catches `rm -rf /`, force-pushes to main,
``--no-verify`` commits, ``curl | sh``, and similar one-shot footguns. It is
NOT a security boundary; treat it as a confirmation step the operator can
override by typing the command themselves.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision

HANDLER = "dangerous_bash"
DOC = "docs/quality-standards.md#destructive-commands"

# (rule_id, predicate, reason). Predicate takes the command string.
_RM_RF_ROOT = re.compile(
    r"\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s+/(?:\s|$|[^.\w])"
)
_GIT_PUSH = re.compile(r"\bgit\s+push\b")
_GIT_FORCE = re.compile(r"(?<!-)(?:--force(?!\-with\-lease)|(?:^|\s)-f(?:\s|$))")
_GIT_PROTECTED_BRANCH = re.compile(r"\b(?:main|master)\b")
_NO_VERIFY = re.compile(r"\bgit\s+(?:commit|push)\b[^\n]*--no-verify\b")
_CURL_PIPE_SH = re.compile(r"\bcurl\b[^\n|]*\|\s*(?:bash|sh|zsh)\b")
_GIT_RESET_HARD = re.compile(r"\bgit\s+reset\s+--hard\b")


def _force_push_to_protected(cmd: str) -> bool:
    """True if the command is a force-push to main/master in any flag order.

    Whitelists ``--force-with-lease`` (the safe alternative).
    """
    if not _GIT_PUSH.search(cmd):
        return False
    if not _GIT_PROTECTED_BRANCH.search(cmd):
        return False
    # Treat --force-with-lease as safe.
    if "--force-with-lease" in cmd:
        return False
    return bool(_GIT_FORCE.search(cmd))


def check(ctx: HookContext) -> Decision:  # noqa: PLR0911  -- one return per dangerous-pattern category
    """Return a deny if the bash command matches a danger pattern."""
    if not ctx.is_bash or ctx.command is None:
        return Decision.allow(HANDLER)
    cmd = ctx.command

    if _RM_RF_ROOT.search(cmd):
        return Decision.deny(
            handler=HANDLER,
            rule_id="BASH-001",
            why="rm -rf at root path. Refusing.",
            fix="Run the command yourself if you really need it.",
            doc=DOC,
        )
    if _force_push_to_protected(cmd):
        return Decision.deny(
            handler=HANDLER,
            rule_id="BASH-002",
            why="Force-push to main/master. Use a feature branch + PR.",
            fix=(
                "Use --force-with-lease at minimum, and prefer pushing a feature "
                "branch and opening a PR."
            ),
            doc=DOC,
        )
    if _NO_VERIFY.search(cmd):
        return Decision.deny(
            handler=HANDLER,
            rule_id="BASH-003",
            why="--no-verify bypasses guardrails. Fix the failing hook instead.",
            fix="Run the command yourself if you really need it.",
            doc=DOC,
        )
    if _CURL_PIPE_SH.search(cmd):
        return Decision.deny(
            handler=HANDLER,
            rule_id="BASH-004",
            why="curl | sh executes untrusted code. Download, inspect, then run.",
            fix="Run the command yourself if you really need it.",
            doc=DOC,
        )
    if _GIT_RESET_HARD.search(cmd):
        return Decision.deny(
            handler=HANDLER,
            rule_id="BASH-005",
            why="git reset --hard discards uncommitted work. Confirm with operator first.",
            fix="Run the command yourself if you really need it.",
            doc=DOC,
        )
    return Decision.allow(HANDLER)
