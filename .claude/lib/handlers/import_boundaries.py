"""Enforce module boundaries.

Rules:
  * Routes & feature code may not reach into ``$lib/design-system/internal``.
  * Frontend code may not import from ``backend`` or ``pipeline`` packages.
  * Backend code may not import from frontend.

The enforcement is regex-based on the new content, not a full import graph
— good enough for the agent boundary; CI does the deeper check.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision
from ..paths import is_design_system_file, is_in_frontend

HANDLER = "import_boundaries"
RULE_ID = "BND-001"
DOC = "docs/quality-standards.md#imports--boundaries"

_INTERNAL_IMPORT = re.compile(r"""(?:from|import)\s+["']\$lib/design-system/internal["']""")
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
                    "Imported from $lib/design-system/internal — that path is "
                    "private to the design system."
                ),
                fix="Import from $lib/design-system (the public barrel) instead.",
                doc=DOC,
            )
        # Frontend may not import backend / pipeline packages.
        if _BACKEND_FROM_FRONTEND.search(content):
            return Decision.deny(
                handler=HANDLER,
                rule_id="BND-002",
                why="Frontend code cannot import backend/pipeline Python packages.",
                fix="Talk to the backend over HTTP via $lib/server/api-client.ts.",
                doc=DOC,
            )

    return Decision.allow(HANDLER)
