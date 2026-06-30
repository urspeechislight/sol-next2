"""Shared filesystem access for static-data repositories.

Keeps the path resolution + error semantics in one place so every repository
module resolves files under the top-level ``data/`` directory the same way.
The repo root + ``data/`` location come from ``core.paths`` (the single
anchor); ``data_path`` is re-exported here for the repositories that import it.
JSON files are loaded once per process at first call (``load_json``); built
SQLite artifacts are opened read-only + immutable once per process here too
(``open_ro_db``), so every repository opens its artifact identically.
"""

from __future__ import annotations

import json
import sqlite3
from functools import cache
from typing import Any

from backend.core.logging import get_logger
from backend.core.paths import data_path

__all__ = ["DataLoadError", "data_path", "load_json", "open_ro_db"]

_logger = get_logger("shia-library.data-loader")


class DataLoadError(RuntimeError):
    """Raised when a static data file is missing or malformed."""


@cache
def open_ro_db(file_name: str, missing_hint: str) -> sqlite3.Connection:
    """Open a built SQLite artifact under ``data/`` read-only + immutable, cached
    once per process (per file). The one place the read-only open shape lives, so
    every repository opens its artifact identically. Raises ``DataLoadError``
    (pointing at the build step) when the artifact has not been materialized yet.
    """
    path = data_path(file_name)
    if not path.exists():
        _logger.error("db-artifact-missing", file=str(path))
        raise DataLoadError(f"{missing_hint} ({path} is missing).")
    con = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


@cache
def load_json(file_name: str) -> Any:
    """Load and cache one JSON file from the repo-root ``data/`` directory.

    Raises ``DataLoadError`` (chained) on any IO or parse failure so the
    caller can fail fast rather than serving silently-empty data.
    """
    path = data_path(file_name)
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        _logger.error("data-file-missing", file=str(path), exc_info=True)
        raise DataLoadError(f"Required data file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        _logger.error("data-file-malformed", file=str(path), exc_info=True)
        raise DataLoadError(f"Data file is not valid JSON: {path}") from exc
