"""Block ``print(...)`` in production Python code; use ``structlog`` instead.

Why: ``print`` bypasses the structured-logging contract — output is
unstructured, has no level, no context, no log-shipping. Production code
must log via ``structlog`` so observability tooling sees consistent records.

Allowed: scripts/, tests/, .claude/, anything imported as `__main__`. Block
inside src/backend/, src/pipeline/, src/frontend/ Python files (rare).
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision
from ..paths import is_in

HANDLER = "no_print"
RULE_ID = "QUAL-013"
DOC = "docs/quality-standards.md#code-quality"

_PRINT = re.compile(r"^\s*print\s*\(", re.MULTILINE)
_PRODUCTION_DIRS = ("src/backend", "src/pipeline")


def check(ctx: HookContext) -> Decision:
    """Return a deny if a top-level ``print(`` appears in production code."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    if not is_in(ctx.file_path, *_PRODUCTION_DIRS):
        return Decision.allow(HANDLER)
    if _PRINT.search(ctx.new_content):
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why="`print(...)` in production code bypasses structured logging.",
            fix=(
                "Use `structlog.get_logger(__name__).info(...)` (or .warning/.error). "
                "Scripts under scripts/ may use print freely."
            ),
            doc=DOC,
        )
    return Decision.allow(HANDLER)
