"""Pipeline phase errors.

Every phase fails loud through this family rather than producing output on
bad input. These lived in serving ``core.errors`` before the pipeline owned
its own package surface; the serving layer keeps only the errors its HTTP
handlers map (``ResourceNotFoundError``), and nothing under ``api/`` or
``repositories/`` imports from here, preserving the artifact-only seam.
"""

from __future__ import annotations


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


class ExtractError(PipelineError):
    """Raised when the extract phase hits an unrecoverable structural error.

    Covers a behavior with no atomicizer rule, an unknown atomicizer strategy or
    extractor name, an invalid entity type, and a content span that produces zero
    units. Each is a bug the pipeline surfaces rather than papering over.
    """
