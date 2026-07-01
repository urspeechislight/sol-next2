"""Domain-level errors. Mapped to HTTP responses by main.py exception handlers."""

from __future__ import annotations


class ResourceNotFoundError(Exception):
    """A repository was asked for a resource that doesn't exist."""

    def __init__(self, *, kind: str, identifier: str) -> None:
        super().__init__(f"No {kind} with identifier={identifier!r}.")
        self.kind = kind
        self.identifier = identifier


class PipelineError(Exception):
    """Base class for ported-pipeline phase errors (segment, extract, ...)."""


class ConfigError(PipelineError):
    """Raised when the ported pipeline config (config/sol.yaml) is missing,
    unreadable, or fails structural validation.

    The pipeline fails loud at startup rather than running on a partially-valid
    config; every phase trusts the frozen Config this loader produces.
    """


class SegmentError(PipelineError):
    """Raised when the segment phase hits an unrecoverable structural error.

    Covers FSM invalid state, a missing config rule for a span type, and the
    failure-budget being exceeded (too many spans routed without an explicit rule).
    """


class ContractError(PipelineError):
    """Raised when a phase contract is violated.

    A manuscript missing the prerequisites a phase requires, or a phase run out
    of order. The pipeline fails loud rather than producing output on bad input.
    """
