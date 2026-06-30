#!/usr/bin/env python3
"""PostToolUse hook for Write|Edit|MultiEdit.

Runs after the file is on disk. Currently invokes ``ruff check`` against
the written Python file (advisory). Extend with prettier / svelte-check /
eslint wrappers as you wire them.
"""

from __future__ import annotations

import _bootstrap  # noqa: F401  # pyright: ignore[reportUnusedImport] — runs the Python version check
from lib import dispatcher
from lib.handlers import post_ruff


def main() -> None:
    """Run all PostToolUse:Write handlers in order."""
    dispatcher.run(event="PostToolUse:Write", handlers=[post_ruff.check])


if __name__ == "__main__":
    main()
