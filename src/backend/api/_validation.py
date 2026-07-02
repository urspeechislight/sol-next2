"""Shared closed-set query validation for taxonomy-valued parameters.

The taxonomy's domains/categories are data, not code, so FastAPI cannot
enforce them as ``Literal`` sets the way it does for modes and fields. This
helper is the one place an unknown taxonomy value becomes a 422 instead of
silently filtering to an empty list; the works and search routes both use it.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException

from backend.core.http import status


def reject_unknown(param: str, value: str | None, predicate: Callable[[str], bool]) -> None:
    """Reject an unknown closed-set query value with 422, matching the FastAPI
    validation-error convention of the ``Literal`` params. No-op when the
    value is absent (``None`` or ``''``)."""
    if value and not predicate(value):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown {param}: {value!r}.",
        )
