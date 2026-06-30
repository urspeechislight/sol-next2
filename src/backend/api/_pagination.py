"""Shared pagination Query parameters for list routes.

The bounded ``limit`` + ``offset`` pair is declared once here and pulled into a
handler via ``Annotated[PageParams, Depends()]``, so the bounds + descriptions
are not copy-pasted into every list route.
"""

from __future__ import annotations

from fastapi import Query

from backend.core.constants import HTTP__DEFAULT_PAGE_SIZE, HTTP__MAX_PAGE_SIZE


class PageParams:
    """``limit`` (1..max) + ``offset`` (>=0) request parameters."""

    def __init__(
        self,
        limit: int = Query(
            default=HTTP__DEFAULT_PAGE_SIZE,
            ge=1,
            le=HTTP__MAX_PAGE_SIZE,
            description="Records per page.",
        ),
        offset: int = Query(default=0, ge=0, description="Records to skip."),
    ) -> None:
        self.limit = limit
        self.offset = offset
