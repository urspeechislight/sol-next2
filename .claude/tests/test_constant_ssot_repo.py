"""Repo-wide invariant: no cross-file constant duplication.

The always-on partner to the write-time ``constant_sprawl`` gate. The gate only
sees the file being written; this asserts the whole tree stays clean, so a
duplicate that predates the gate or lands through a bypass is caught in CI.
"""

from __future__ import annotations

from lib import paths
from lib.handlers import constant_sprawl


def test_should_have_no_cross_file_constant_duplication() -> None:
    """Every constant name, value, and string vocabulary lives in one module repo-wide."""
    collisions = constant_sprawl.repo_wide_collisions(paths.REPO_ROOT)
    assert collisions == [], "cross-file constant duplication found:\n" + "\n".join(collisions)
