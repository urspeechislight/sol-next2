"""Dev-only extraction-inspection routes (``/dev/extraction/*``).

The surface a developer or admin uses to validate what segment+extract
produced for a book: the artifact's books with coverage summaries, and one
page's spans/units/entities near-raw. Regular users never reach these routes:
every request passes the router-level ``_require_dev_tools`` dependency,
which 404s unless the deployment opted in with ``SOL_DEV_TOOLS=true``. The
routes stay registered (and in the exported OpenAPI schema) regardless, so
the generated frontend types do not depend on the environment.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.api._routes import get_route
from backend.core.http import status
from backend.core.settings import get_settings
from backend.models.errors import ErrorEnvelope
from backend.models.extraction import (
    ExtractionBookSummary,
    ExtractionEntryAudit,
    ExtractionPage,
)
from backend.repositories import extraction as extraction_repo


def _require_dev_tools() -> None:
    """404 unless this deployment enabled the dev tools (SOL_DEV_TOOLS=true)."""
    if not get_settings().dev_tools:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dev tools are disabled on this deployment (SOL_DEV_TOOLS).",
        )


router = APIRouter(tags=["extraction"], dependencies=[Depends(_require_dev_tools)])

_DEV_TOOLS_404: dict[int | str, dict[str, Any]] = {
    404: {
        "model": ErrorEnvelope,
        "description": "Dev tools are disabled on this deployment (SOL_DEV_TOOLS unset); "
        "declared so generated client types represent what callers actually see.",
    }
}

get_route(
    router,
    "/dev/extraction/books",
    extraction_repo.extraction_summaries,
    response_model=list[ExtractionBookSummary],
    summary="List the books in the manuscript artifact with extraction coverage.",
    responses=_DEV_TOOLS_404,
)
get_route(
    router,
    "/dev/extraction/books/{book_urn}/pages/{page_number}",
    extraction_repo.page_extraction,
    response_model=ExtractionPage,
    summary="Get one page's spans, units, and entities near-raw, for validation.",
    responses=_DEV_TOOLS_404,
)
get_route(
    router,
    "/dev/extraction/books/{book_urn}/entry-audit",
    extraction_repo.entry_audit,
    response_model=ExtractionEntryAudit,
    summary="Audit extracted units against the edition's printed entry numbers, per section.",
    responses=_DEV_TOOLS_404,
)
