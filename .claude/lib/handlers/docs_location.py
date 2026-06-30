"""Enforce: all documentation lives in ``docs/``.

Allowed `.md` outside docs/:
  * ``README.md`` and ``CLAUDE.md`` at repo root (entry points).
  * Anything inside ``.github/`` (issue templates, etc.).
  * Inside ``node_modules/``, ``.venv/``, ``build/`` (vendored).
  * Claude Code capability definitions under ``.claude/agents/`` (subagent
    defs) and ``.claude/skills/`` (skill bundles). These are markdown *by
    design* and are discovered by Claude Code only at those exact paths, so
    they are configuration, not documentation. Kept narrow: any other stray
    markdown under ``.claude/`` is still blocked.

Everything else gets blocked, with a fix that points at the docs/ folder.
"""

from __future__ import annotations

from .. import paths as _paths
from ..context import HookContext
from ..decision import Decision

HANDLER = "docs_location"
RULE_ID = "DOC-001"
DOC = "docs/repo-layout.md#documentation"

_ALLOWED_TOP_LEVEL = {"README.md", "CLAUDE.md"}
_ALLOWED_PREFIXES = ("docs/", ".github/", "node_modules/", ".venv/", "build/", ".svelte-kit/")
# Claude Code discovers subagent and skill definitions only at these paths;
# they are capability config (markdown by design), not documentation.
_ALLOWED_CLAUDE_DEFS = (".claude/agents/", ".claude/skills/")


def check(ctx: HookContext) -> Decision:
    """Return a deny if a markdown doc is being written outside docs/."""
    if not ctx.is_write or ctx.file_path is None or ctx.suffix != "md":
        return Decision.allow(HANDLER)

    try:
        rel = ctx.file_path.resolve().relative_to(_paths.REPO_ROOT).as_posix()
    except ValueError:
        return Decision.allow(HANDLER)

    if rel in _ALLOWED_TOP_LEVEL:
        return Decision.allow(HANDLER)
    if rel.startswith(_ALLOWED_PREFIXES):
        return Decision.allow(HANDLER)
    if rel.startswith(_ALLOWED_CLAUDE_DEFS):
        return Decision.allow(HANDLER)

    # Allow inline LICENSE files, etc.
    if rel.upper().startswith(("LICENSE", "NOTICE", "CHANGELOG")):
        return Decision.allow(HANDLER)

    return Decision.deny(
        handler=HANDLER,
        rule_id=RULE_ID,
        why=f"Markdown file `{rel}` is outside docs/. All documentation lives in docs/.",
        fix=f"Move this content to docs/{ctx.file_path.name}.",
        doc=DOC,
    )
