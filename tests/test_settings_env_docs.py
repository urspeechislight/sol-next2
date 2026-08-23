"""Freshness gate for the env inventory: every Settings field must appear in
``.env.example``, and ``.env.example`` must not document a name Settings does
not read.

``core/settings.py`` is the only place the environment is read, so a field
without a documented ``SOL_*`` line is undiscoverable for a fresh deploy, and
a documented line without a field is stale drift. Same freshness-gate idea as
``types:check`` (OpenAPI vs client), applied to configuration.
"""

from __future__ import annotations

from backend.core.paths import REPO_ROOT
from backend.core.settings import Settings

# SOL_* names consumed outside Pydantic Settings: SOL_API_TARGET is read by
# the frontend's vite.config.ts, never the backend.
FRONTEND_ONLY = {"SOL_API_TARGET"}


def _documented() -> set[str]:
    """Every SOL_* name present in .env.example, commented lines included."""
    names: set[str] = set()
    for line in (REPO_ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        name, sep, _ = line.lstrip("#").strip().partition("=")
        name = name.strip()
        if sep and name.startswith("SOL_") and name.isupper():
            names.add(name)
    return names


def _fields() -> set[str]:
    return {f"SOL_{name.upper()}" for name in Settings.model_fields}


def test_should_document_every_settings_field_in_env_example() -> None:
    missing = _fields() - _documented()
    assert not missing, f"Settings fields with no .env.example line: {sorted(missing)}"


def test_should_reject_env_example_vars_not_in_settings() -> None:
    stale = _documented() - _fields() - FRONTEND_ONLY
    assert not stale, f".env.example names Settings does not read: {sorted(stale)}"
