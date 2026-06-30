"""Tiny bootstrap so dispatch scripts can `from lib.* import ...`.

Each script under ``.claude/hooks/`` imports this module first. It also
enforces the minimum Python version — handlers use 3.10+ features
(``match``, ``dataclass(slots=True)``, parameterized generics).

Failure mode: if ``python3`` is too old, the hook prints a one-line error to
stderr and exits non-zero. Claude Code surfaces the message and aborts the
tool call (fail-closed — better to block than silently bypass guardrails).
"""

from __future__ import annotations

import sys
from pathlib import Path

MIN_PYTHON: tuple[int, int] = (3, 10)


def _enforce_python_version() -> None:
    """Exit non-zero if the running Python is older than MIN_PYTHON."""
    if sys.version_info < MIN_PYTHON:
        actual = ".".join(str(p) for p in sys.version_info[:3])
        required = ".".join(str(p) for p in MIN_PYTHON)
        print(
            f"sol-next1 harness requires Python {required}+, found {actual} at {sys.executable}.",
            file=sys.stderr,
        )
        print(
            "Install a newer Python (e.g. via `uv python install 3.12`) and "
            "ensure `python3 --version` reports >= " + required + ".",
            file=sys.stderr,
        )
        sys.exit(2)


_enforce_python_version()

_CLAUDE_DIR = Path(__file__).resolve().parent.parent
if str(_CLAUDE_DIR) not in sys.path:
    sys.path.insert(0, str(_CLAUDE_DIR))
