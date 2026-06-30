"""Append-only audit log for hook events.

Every tool-call decision is appended as a JSON line to
``.claude/audit/events.jsonl``. The log:
  • Rotates at ``MAX_BYTES`` (default 8 MB) — older log moves to
    ``events.jsonl.<unix-ts>``.
  • Uses ``fcntl.flock`` on POSIX so concurrent hook invocations don't
    interleave lines.
  • Failures here are swallowed (``audit-write-failed`` to stderr) — auditing
    must not affect the agent's tool result.
"""

from __future__ import annotations

import json
import os
import sys
import time
import types
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path

from .decision import Decision

AUDIT_DIR = Path(__file__).resolve().parent.parent / "audit"
AUDIT_PATH = AUDIT_DIR / "events.jsonl"
MAX_BYTES = 8 * 1024 * 1024  # 8 MB — recent history in primary log

try:
    import fcntl as _fcntl_module
except ImportError:  # pragma: no cover — non-POSIX
    fcntl: types.ModuleType | None = None
else:
    fcntl = _fcntl_module


def append(
    *,
    event: str,
    tool_name: str,
    payload: Mapping[str, object],
    decisions: list[Decision],
    blocked: bool,
) -> None:
    """Append one record to the audit log. Failures here are swallowed."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": time.time(),
        "event": event,
        "tool_name": tool_name,
        "session_id": os.environ.get("CLAUDE_SESSION_ID", ""),
        "blocked": blocked,
        "decisions": [asdict(d) for d in decisions if d.severity != "allow"],
        "target": _extract_target(payload),
    }
    line = json.dumps(record) + "\n"

    try:
        _rotate_if_needed()
        with AUDIT_PATH.open("a", encoding="utf-8") as fh:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                fh.write(line)
                fh.flush()
            finally:
                if fcntl is not None:
                    with suppress(OSError):
                        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError as e:  # pragma: no cover — best-effort
        print(f"audit-write-failed: {e}", file=sys.stderr)


def _rotate_if_needed() -> None:
    """If the active log exceeds MAX_BYTES, rotate it to events.jsonl.<ts>."""
    try:
        size = AUDIT_PATH.stat().st_size
    except FileNotFoundError:
        return
    if size < MAX_BYTES:
        return
    rotated = AUDIT_DIR / f"events.jsonl.{int(time.time())}"
    with suppress(OSError):
        AUDIT_PATH.rename(rotated)


def _extract_target(payload: Mapping[str, object]) -> str:
    """Pull a sensible 'target' string out of the tool payload for the log."""
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, Mapping):
        return ""
    for key in ("file_path", "command", "url", "pattern"):
        value = tool_input.get(key)  # type: ignore[misc]  -- Mapping value type is object
        if isinstance(value, str) and value:
            return value
    return ""
