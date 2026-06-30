#!/usr/bin/env python3
"""SessionStart hook.

Two outputs, neither blocking (exit 0):

  * a short rules banner to **stderr** (shown to the operator);
  * a symbol inventory of ``src/`` emitted as ``additionalContext`` JSON on
    **stdout**, which Claude Code injects into the session context so the agent
    starts each session knowing what already exists — reuse before re-create,
    the proactive companion to the function_duplication handler.
"""

from __future__ import annotations

import json
import sys

import _bootstrap  # noqa: F401  # pyright: ignore[reportUnusedImport] — runs the Python version check
from lib.inventory import build_symbol_inventory

BANNER = """
╭─ sol-next2 harness active ──────────────────────────────────────────────╮
│  · Design tokens are SSOT (frontend/src/lib/design-system/tokens.css)   │
│  · No raw colors / inline styles / ad-hoc variant maps                  │
│  · Reuse existing symbols — duplicates blocked (DRY-001/002/003)        │
│  · All docs go in docs/                                                 │
│  · See CLAUDE.md and docs/quality-standards.md for the full ruleset     │
╰─────────────────────────────────────────────────────────────────────────╯
""".strip()


def main() -> None:
    """Print the banner (stderr) and the symbol inventory (stdout additionalContext)."""
    print(BANNER, file=sys.stderr)
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": build_symbol_inventory(),
        }
    }
    print(json.dumps(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
