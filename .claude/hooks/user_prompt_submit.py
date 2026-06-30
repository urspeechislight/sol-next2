#!/usr/bin/env python3
"""UserPromptSubmit hook.

Reserved for future use (e.g., reminding the agent of conventions when a
prompt looks like it might cause SSOT violations). Currently passes through.
"""

from __future__ import annotations

import sys

import _bootstrap  # noqa: F401  # pyright: ignore[reportUnusedImport] — runs the Python version check


def main() -> None:
    """Pass through — no-op for now."""
    sys.exit(0)


if __name__ == "__main__":
    main()
