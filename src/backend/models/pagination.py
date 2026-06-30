"""Generic pagination envelope for list endpoints.

Why a typed envelope rather than a raw list: clients need to know the
total when 18.7k books no longer fit in one response. Keep the shape
boring and consistent across every paginated endpoint.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Page[T](BaseModel):
    """One slice of a larger collection."""

    model_config = ConfigDict(frozen=True)

    items: list[T] = Field(description="Records in this slice.")
    total: int = Field(ge=0, description="Total records matching the query, across all pages.")
    limit: int = Field(ge=1, description="Slice size requested.")
    offset: int = Field(ge=0, description="Number of records skipped before this slice.")
