#!/usr/bin/env python3
"""PreToolUse hook for Read|Grep|Glob.

Currently advisory-only — logs the access for audit. Wave D will add
sensitive-path detection (e.g., reading ``.env``, private keys).
"""

from __future__ import annotations

import _bootstrap  # noqa: F401  # pyright: ignore[reportUnusedImport] — runs the Python version check
from lib import dispatcher
from lib.handlers import sensitive_read


def main() -> None:
    """Run all PreToolUse:Read handlers in order."""
    dispatcher.run(event="PreToolUse:Read", handlers=[sensitive_read.check])


if __name__ == "__main__":
    main()
