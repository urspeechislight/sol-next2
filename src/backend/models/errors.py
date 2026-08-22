"""The one error-response envelope, so every declared failure response has a
shape (and the generated frontend types can represent it)."""

from __future__ import annotations

from pydantic import Field

from backend.models._base import FrozenModel


class ErrorEnvelope(FrozenModel):
    """The body of every non-2xx response the API declares."""

    detail: str = Field(description="Human-readable failure description.")
