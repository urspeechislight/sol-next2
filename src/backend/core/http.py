"""HTTP-related named constants and helpers.

We re-export ``starlette.status`` codes here as the canonical home so the
``centralization`` rule has a single allowed location for HTTP-status
references — anywhere else uses ``from src.backend.core.http import status``.
"""

from __future__ import annotations

from starlette import status

__all__ = ["status"]
