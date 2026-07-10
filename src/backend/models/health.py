"""DTOs for the aggregate health probe.

``/api/health`` exercises each major subsystem so a client heartbeat can tell a
"backend up but a data source is broken" state from an outright unreachable
backend. The liveness probe (``/health``) only reports that the process is up.
"""

from __future__ import annotations

from pydantic import Field

from backend.models._base import FrozenModel


class HealthCheck(FrozenModel):
    """One subsystem's probe result."""

    name: str = Field(description="The subsystem probed (domains, books, rijal, ...).")
    ok: bool = Field(description="True when the probe read succeeded.")
    error: str = Field(default="", description="Failure detail when the probe raised.")


class HealthReport(FrozenModel):
    """The aggregate result: ``ok`` only when every subsystem answered."""

    status: str = Field(description="'ok' when every check passed, else 'degraded'.")
    checks: list[HealthCheck] = Field(description="Per-subsystem probe results.")
