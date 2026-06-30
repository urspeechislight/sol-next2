"""FastAPI application entry point.

Wires up:
  * health/liveness/readiness endpoints (the only routes permitted here
    by CENTRAL-017),
  * CORS so the Vite frontend on :8765 can call this API on :8001,
  * the API router from ``src.backend.api`` once endpoints exist.

Routes + the not-found handler register via ``add_api_route`` /
``add_exception_handler`` (the project's one registration style).
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import api_router
from backend.core.errors import ResourceNotFoundError
from backend.core.http import status
from backend.core.logging import configure_logging, get_logger
from backend.core.settings import get_settings


async def _not_found(_request: Request, exc: Exception) -> JSONResponse:
    """Map a ResourceNotFoundError to a 404 JSON body.

    Registered only for ResourceNotFoundError; anything else reaching here is a
    wiring bug and is re-raised rather than masked behind a generic 404.
    """
    if not isinstance(exc, ResourceNotFoundError):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"No {exc.kind} with identifier={exc.identifier!r}."},
    )


async def _health() -> dict[str, str]:
    """Container health probe — succeeds when the process is up."""
    return {"status": "ok"}


async def _livez() -> dict[str, str]:
    """Kubernetes liveness probe."""
    return {"status": "alive"}


async def _readyz() -> dict[str, str]:
    """Kubernetes readiness probe."""
    return {"status": "ready"}


_health_router = APIRouter(tags=["health"])
for _path, _endpoint in (("/health", _health), ("/livez", _livez), ("/readyz", _readyz)):
    _health_router.add_api_route(_path, _endpoint, methods=["GET"], status_code=status.HTTP_200_OK)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(level=settings.log_level)
    logger = get_logger("shia-library.main")
    logger.info("startup", cors_origins=settings.cors_allowed_origins)

    app = FastAPI(
        title="Shia Online Library",
        description="Knowledge-graph reader for classical Arabic manuscripts.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.add_exception_handler(ResourceNotFoundError, _not_found)
    app.include_router(_health_router)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
