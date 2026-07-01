"""Domain-level errors. Mapped to HTTP responses by main.py exception handlers."""

from __future__ import annotations


class ResourceNotFoundError(Exception):
    """A repository was asked for a resource that doesn't exist."""

    def __init__(self, *, kind: str, identifier: str) -> None:
        super().__init__(f"No {kind} with identifier={identifier!r}.")
        self.kind = kind
        self.identifier = identifier


class ConfigError(Exception):
    """Raised when the ported pipeline config (config/sol.yaml) is missing,
    unreadable, or fails structural validation.

    The pipeline fails loud at startup rather than running on a partially-valid
    config; every phase trusts the frozen Config this loader produces.
    """
