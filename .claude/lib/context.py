"""Tool-call context: typed view of the JSON payload passed via stdin.

Claude Code dispatches hooks with a JSON payload like::

    {
      "session_id": "...",
      "tool_name": "Edit",
      "tool_input": {"file_path": "/a/b/foo.svelte", "old_string": "...", "new_string": "..."},
      "tool_response": null
    }

Handlers receive a :class:`HookContext` constructed from this payload.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

# Payload values come from JSON parsing — `object` is honest about
# "we don't know the type without checking." Pyright then narrows
# correctly through isinstance checks instead of propagating `Any`.
JsonValue = object
HookPayload = Mapping[str, JsonValue]


def _as_dict(value: JsonValue) -> Mapping[str, JsonValue]:
    """Return value as a Mapping[str, object] if it is one, else empty."""
    if isinstance(value, Mapping):
        # Filter to string keys; tool_input is always JSON-object so this
        # is a defensive cast, not a real-world filter.
        return {str(k): v for k, v in value.items()}  # type: ignore[misc]
    return {}


def _as_str(value: JsonValue) -> str | None:
    """Return value if it is a string, else None."""
    return value if isinstance(value, str) else None


def _multiedit_pieces(edits: JsonValue) -> str | None:
    """Concatenate `new_string` fields from a MultiEdit `edits` list."""
    if not isinstance(edits, list):
        return None
    pieces: list[str] = []
    for e in edits:  # type: ignore[reportUnknownVariableType]
        if isinstance(e, Mapping):
            ns = e.get("new_string")  # type: ignore[misc]
            if isinstance(ns, str):
                pieces.append(ns)
    return "\n".join(pieces) if pieces else None


@dataclass(frozen=True, slots=True)
class HookContext:
    """Normalized view of a tool-call payload."""

    tool_name: str
    file_path: Path | None
    command: str | None
    new_content: str | None
    old_content: str | None
    raw: HookPayload = field(default_factory=lambda: {})  # noqa: PIE807

    @property
    def suffix(self) -> str:
        """File extension without the leading dot, lowercase."""
        return self.file_path.suffix.lstrip(".").lower() if self.file_path else ""

    @property
    def is_write(self) -> bool:
        """True if this is a Write/Edit/MultiEdit operation."""
        return self.tool_name in {"Write", "Edit", "MultiEdit"} and self.file_path is not None

    @property
    def is_bash(self) -> bool:
        """True if this is a Bash command."""
        return self.tool_name == "Bash" and self.command is not None

    @staticmethod
    def from_payload(payload: HookPayload) -> HookContext:
        """Construct a HookContext from the raw stdin payload."""
        tool_name = str(payload.get("tool_name", ""))
        tool_input = _as_dict(payload.get("tool_input", {}))

        fp_raw = _as_str(tool_input.get("file_path"))
        file_path = Path(fp_raw).resolve() if fp_raw else None
        command = _as_str(tool_input.get("command"))

        new_content: str | None = None
        if tool_name == "Write":
            new_content = _as_str(tool_input.get("content"))
        elif tool_name == "Edit":
            new_content = _as_str(tool_input.get("new_string"))
        elif tool_name == "MultiEdit":
            new_content = _multiedit_pieces(tool_input.get("edits"))

        old_content: str | None = None
        if tool_name == "Edit":
            old_content = _as_str(tool_input.get("old_string"))

        return HookContext(
            tool_name=tool_name,
            file_path=file_path,
            command=command,
            new_content=new_content,
            old_content=old_content,
            raw=payload,
        )
