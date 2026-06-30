#!/usr/bin/env python3
"""PreToolUse hook for Bash.

Catches obviously dangerous shell commands. Not a security boundary —
treat it as a confirmation step the operator can override.
"""

from __future__ import annotations

import _bootstrap  # noqa: F401  # pyright: ignore[reportUnusedImport]
from lib import dispatcher
from lib.handlers import bash_file_write, dangerous_bash


def main() -> None:
    """Run all PreToolUse:Bash handlers in order."""
    dispatcher.run(
        event="PreToolUse:Bash",
        handlers=[dangerous_bash.check, bash_file_write.check],
    )


if __name__ == "__main__":
    main()
