"""Domain-level errors. Mapped to HTTP responses by main.py exception handlers."""

from __future__ import annotations


class ResourceNotFoundError(Exception):
    """A repository was asked for a resource that doesn't exist."""

    def __init__(self, *, kind: str, identifier: str) -> None:
        super().__init__(f"No {kind} with identifier={identifier!r}.")
        self.kind = kind
        self.identifier = identifier


class CorpusSearchError(RuntimeError):
    """Raised when the consolidated search backend fails or answers outside contract.

    Carries enough context to debug the failure; main.py maps it to a 503 so a
    backend outage is visible rather than silently swallowed.
    """
