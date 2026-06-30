"""Enforce module boundaries.

Rules:
  * Routes & feature code may not reach into ``design-system/internal``.
  * Frontend code may not import from ``backend`` or ``pipeline`` packages.
  * Backend code may not import from frontend.

The enforcement is regex-based on the new content, not a full import graph,
which is good enough for the agent boundary; CI does the deeper check.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision
from ..paths import is_design_system_file, is_in_frontend

HANDLER = "import_boundaries"
RULE_ID = "BND-001"
DOC = "docs/quality-standards.md#imports--boundaries"

# Any import whose path ends at design-system/internal, whether written as a
# relative path (../lib/design-system/internal, which the React frontend uses)
# or through an alias.
_INTERNAL_IMPORT = re.compile(r"""(?:from|import)\s+["'][^"']*design-system/internal["']""")
_BACKEND_FROM_FRONTEND = re.compile(r"""(?:from|import)\s+["'](?:backend|pipeline)(?:\.|/|["'])""")


def check(ctx: HookContext) -> Decision:
    """Return a deny if boundary-crossing imports appear."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)

    content = ctx.new_content

    if is_in_frontend(ctx.file_path):
        # Routes / feature code cannot reach internal/.
        if not is_design_system_file(ctx.file_path) and _INTERNAL_IMPORT.search(content):
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    "Imported from design-system/internal, which is private to "
                    "the design system."
                ),
                fix="Import from the design-system barrel (../lib/design-system) instead.",
                doc=DOC,
            )
        # Frontend may not import backend / pipeline packages.
        if _BACKEND_FROM_FRONTEND.search(content):
            return Decision.deny(
                handler=HANDLER,
                rule_id="BND-002",
                why="Frontend code cannot import backend/pipeline Python packages.",
                fix="Talk to the backend over HTTP through the lib/api client.",
                doc=DOC,
            )

    return Decision.allow(HANDLER)
