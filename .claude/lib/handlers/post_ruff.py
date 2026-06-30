"""PostToolUse: run ruff against the just-written Python file.

This is the on-disk verification layer. PreToolUse runs cheap content-only
checks before the file lands; this runs the actual linter after. Failure
becomes an advisory — the file is already on disk; demanding a re-write
would require a separate Edit cycle. The advisory tells the agent to fix it.

Why advisory and not block: blocking after-the-fact creates inconsistent
state (file written, hook said no). The next Edit will either include the
fix or hit the PreToolUse layer.
"""

from __future__ import annotations

import shutil
import subprocess

from ..context import HookContext
from ..decision import Decision

HANDLER = "post_ruff"
RULE_ID = "QUAL-020"
DOC = "docs/quality-standards.md#code-quality"


def check(ctx: HookContext) -> Decision:
    """Advise if the just-written Python file fails ``ruff check``."""
    if not ctx.is_write or ctx.file_path is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    ruff = shutil.which("ruff")
    if ruff is None:
        return Decision.allow(HANDLER)

    try:
        proc = subprocess.run(  # noqa: S603  -- ruff is the configured project linter
            [ruff, "check", "--no-cache", str(ctx.file_path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return Decision.allow(HANDLER)

    if proc.returncode == 0:
        return Decision.allow(HANDLER)

    summary = proc.stdout.strip().splitlines()
    first = summary[0] if summary else "ruff check failed"
    return Decision.advise(
        handler=HANDLER,
        rule_id=RULE_ID,
        why=f"ruff flagged the file: {first[:200]}",
        fix="Run `uv run ruff check --fix <file>` and follow up.",
        doc=DOC,
    )
