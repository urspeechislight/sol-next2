"""Block bare ``except:`` and ``except X: pass`` in Python.

Why: silent exception swallowing hides bugs. If you really want to ignore an
error, do it explicitly with a comment that names the exception type and
documents the reason.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision

HANDLER = "no_silent_except"
RULE_ID = "QUAL-012"
DOC = "docs/quality-standards.md#code-quality"

_BARE_EXCEPT = re.compile(r"^\s*except\s*:\s*$", re.MULTILINE)
_PASS_EXCEPT = re.compile(r"except[^\n:]*:\s*\n\s*pass\s*(?:\n|$)")


def check(ctx: HookContext) -> Decision:
    """Return a deny if forbidden except patterns are present in Python files."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    if _BARE_EXCEPT.search(ctx.new_content):
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why="Bare `except:` clause found.",
            fix=(
                "Catch a specific exception class. If you must catch everything, use "
                "`except Exception:` and either log or re-raise — never `pass`."
            ),
            doc=DOC,
        )
    if _PASS_EXCEPT.search(ctx.new_content):
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why="`except: pass` (or equivalent) silently swallows errors.",
            fix=(
                "Log the exception, decide on a recovery path, or let it propagate. "
                "Silent passes hide real bugs."
            ),
            doc=DOC,
        )
    return Decision.allow(HANDLER)
