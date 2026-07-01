"""Filesystem anchors for the repo — the single place the repo root and the
``data/`` directory are located.

Everything that needs an on-disk path under the repo derives it from here:
the settings ``.env`` lookup, the static-data loader, and the build scripts.
The root is computed once so it cannot drift between callers. ``REPO_ROOT``
walks four parents up from this file: ``core/paths.py`` to ``core`` to
``backend`` to ``src`` to the repo root.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR: Final[Path] = REPO_ROOT / "data"


def data_path(file_name: str) -> Path:
    """Return the absolute path of ``file_name`` under the repo-root ``data/``."""
    return DATA_DIR / file_name
