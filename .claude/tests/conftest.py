"""Shared fixtures for harness self-tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Make the .claude/lib package importable regardless of where pytest is invoked.
_CLAUDE_DIR = Path(__file__).resolve().parent.parent
if str(_CLAUDE_DIR) not in sys.path:
    sys.path.insert(0, str(_CLAUDE_DIR))
