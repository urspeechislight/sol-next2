#!/usr/bin/env python3
"""PreToolUse hook for WebFetch|WebSearch.

Logs every external fetch. The handler can also block specific domains
(e.g., known data-exfil endpoints) — currently advisory.
"""

from __future__ import annotations

import _bootstrap  # noqa: F401  # pyright: ignore[reportUnusedImport] — runs the Python version check
from lib import dispatcher
from lib.handlers import web_access


def main() -> None:
    """Run all PreToolUse:Web handlers in order."""
    dispatcher.run(event="PreToolUse:Web", handlers=[web_access.check])


if __name__ == "__main__":
    main()
