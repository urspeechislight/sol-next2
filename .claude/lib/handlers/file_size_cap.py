"""Cap file size — warn at 400 LOC, block at 450 LOC.

Why: large files are a smell that the file is doing too much. Splitting up
front pays back in review velocity and reuse. A file at 400 LOC is the
signal to start splitting; 450 is the hard cap.

These caps are intentionally tighter than the sol-next1 defaults (300/500)
per project standard.
"""

from __future__ import annotations

from ..context import HookContext
from ..decision import Decision

HANDLER = "file_size_cap"
WARN_LOC = 400
BLOCK_LOC = 450
DOC = "docs/quality-standards.md#size-caps"


def _line_count(content: str) -> int:
    """Count non-blank, non-pure-comment lines."""
    return sum(
        1
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "//", "/*", "*"))
    )


def check(ctx: HookContext) -> Decision:
    """Warn / block based on file LOC."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)
    if ctx.suffix not in {"py", "ts", "tsx", "js", "jsx", "svelte"}:
        return Decision.allow(HANDLER)

    loc = _line_count(ctx.new_content)
    if loc >= BLOCK_LOC:
        return Decision.deny(
            handler=HANDLER,
            rule_id="QUAL-010",
            why=f"File is {loc} LOC; hard cap is {BLOCK_LOC}.",
            fix=(
                "Split this file into smaller modules with focused responsibilities. "
                "A file above 400 LOC is the signal to start splitting; 450 is the "
                "hard stop."
            ),
            doc=DOC,
        )
    if loc >= WARN_LOC:
        return Decision.advise(
            handler=HANDLER,
            rule_id="QUAL-010",
            why=f"File is {loc} LOC; soft limit {WARN_LOC}, hard cap {BLOCK_LOC}.",
            fix="Start splitting now — adding more code will block at the hard cap.",
            doc=DOC,
        )
    return Decision.allow(HANDLER)
