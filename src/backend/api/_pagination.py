"""Shared pagination Query parameters for list routes.

The bounded ``limit`` + ``offset`` pair is declared once here. ``page_params``
builds the dependency, parameterized so a route family with its own default
page size or parameter wording (the reader's in-book search) states only what
differs; ``PageDep`` is the standard form every other list route uses via
``page: PageDep``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Query

from backend.core.constants import HTTP__DEFAULT_PAGE_SIZE, HTTP__MAX_PAGE_SIZE


class PageParams:
    """``limit`` (1..max) + ``offset`` (>=0), produced by ``page_params``."""

    def __init__(self, limit: int, offset: int) -> None:
        self.limit = limit
        self.offset = offset


def page_params(
    default_limit: int = HTTP__DEFAULT_PAGE_SIZE,
    limit_description: str = "Records per page.",
    offset_description: str = "Records to skip.",
) -> Callable[..., PageParams]:
    """Build the limit/offset dependency for one route family.

    The bounds are fixed project-wide; the default page size and the parameter
    descriptions are the only legitimate per-family variation.
    """

    def dependency(
        limit: int = Query(
            default=default_limit,
            ge=1,
            le=HTTP__MAX_PAGE_SIZE,
            description=limit_description,
        ),
        offset: int = Query(default=0, ge=0, description=offset_description),
    ) -> PageParams:
        """Bind the validated limit/offset pair into a PageParams."""
        return PageParams(limit, offset)

    return dependency


PageDep = Annotated[PageParams, Depends(page_params())]
