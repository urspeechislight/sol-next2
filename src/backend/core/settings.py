"""Pydantic Settings — the only place ``os.getenv`` / ``os.environ`` is read.

To expose a new env-driven value to the codebase, add a field here and
import ``get_settings().<field>`` from the rest of the app.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.paths import REPO_ROOT


class Settings(BaseSettings):
    """Application settings — all env-driven values live here as typed fields."""

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        env_prefix="SOL_",
        extra="ignore",
    )

    cors_allowed_origins: list[str] = Field(
        default=[
            "http://localhost:8765",
            "http://127.0.0.1:8765",
            "http://10.0.0.10:8765",
        ],
        description="Origins allowed by CORS middleware (the static frontend host).",
    )
    log_level: str = Field(
        default="INFO",
        description="structlog/stdlib log level.",
    )
    books_dir: Path = Field(
        ...,
        description=(
            "Root directory of the upstream book corpus (read-only). "
            "Required: set SOL_BOOKS_DIR in the environment or .env."
        ),
    )
    pipeline_config: Path = Field(
        default=REPO_ROOT / "config" / "sol.yaml",
        description="Path to the ported sol-next pipeline config (config/sol.yaml).",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    pydantic-settings populates the required fields from the environment at
    runtime, which pyright's strict mode cannot see, so the ``reportCallIssue``
    suppression on the constructor call is intentional.
    """
    return Settings()  # pyright: ignore[reportCallIssue]
