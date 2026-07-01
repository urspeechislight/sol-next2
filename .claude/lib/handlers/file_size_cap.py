"""Advise on file size at 400 LOC. Advisory only, never a block.

Why advisory rather than blocking: the old hard cap at 450 manufactured
structure instead of preventing it. Files were split at arbitrary lines into
facade modules and single-importer shards purely to clear the gate, which is
how pipeline/boundaries.py became a 14-line re-export front. A large file is
a redesign signal the author must act on by extracting a real concept; a
mechanical split is never the right response. The advisory keeps the signal
without forcing the wrong fix.
"""

from __future__ import annotations

from ..context import HookContext
from ..decision import Decision

HANDLER = "file_size_cap"
WARN_LOC = 400
DOC = "docs/quality-standards.md#size-caps"


def _line_count(content: str) -> int:
    """Count non-blank, non-pure-comment lines."""
    return sum(
        1
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "//", "/*", "*"))
    )


def check(ctx: HookContext) -> Decision:
    """Advise when a file passes the 400-LOC redesign signal; never block."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)
    if ctx.suffix not in {"py", "ts", "tsx", "js", "jsx"}:
        return Decision.allow(HANDLER)

    loc = _line_count(ctx.new_content)
    if loc >= WARN_LOC:
        return Decision.advise(
            handler=HANDLER,
            rule_id="QUAL-010",
            why=f"File is {loc} LOC; the redesign signal is {WARN_LOC}.",
            fix=(
                "Extract a real concept into its own module. Do not split "
                "mechanically at a line count; a facade plus shards is worse "
                "than one large cohesive file."
            ),
            doc=DOC,
        )
    return Decision.allow(HANDLER)
