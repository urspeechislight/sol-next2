"""Tests for the constant_sprawl handler.

The handler reads sibling .py files from the live repo. To make tests
independent of repo state, we monkeypatch the indexer to return a known
fake set of existing constants.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from lib.context import HookContext
from lib.handlers import constant_sprawl


@pytest.fixture
def fake_index(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Replace the on-disk indexer + path-scope check with deterministic stubs.

    The handler scopes to ``src/`` under the real REPO_ROOT; we don't want
    test fixture paths to depend on the repo's actual checkout location, so
    the scope check is also stubbed.
    """

    def stub(exclude: Path | None) -> tuple[dict[str, Path], dict[object, list[tuple[str, Path]]]]:
        by_name = {
            "TIMEOUT_SECONDS": Path("/repo/src/backend/core/constants.py"),
            "PAGE_SIZE": Path("/repo/src/backend/core/constants.py"),
        }
        by_value: dict[object, list[tuple[str, Path]]] = {
            30: [("TIMEOUT_SECONDS", Path("/repo/src/backend/core/constants.py"))],
            50: [("PAGE_SIZE", Path("/repo/src/backend/core/constants.py"))],
            "shia": [("SECT_SHIA", Path("/repo/src/backend/core/constants.py"))],
        }
        return by_name, by_value

    def always_in_scope(_p: Path | None, *_segs: str) -> bool:
        return True

    monkeypatch.setattr(constant_sprawl, "_index_existing", stub)
    monkeypatch.setattr(constant_sprawl, "is_in", always_in_scope)
    yield


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/repo/src/backend/api/routes.py").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_no_constants_are_added(fake_index: None) -> None:
    """A file with no module-level constants passes."""
    decision = constant_sprawl.check(_ctx("def fn() -> int:\n    return 1\n"))
    assert decision.severity == "allow"


def test_should_block_when_constant_name_collides(fake_index: None) -> None:
    """Re-declaring an existing constant name in a different file is blocked."""
    decision = constant_sprawl.check(_ctx("TIMEOUT_SECONDS = 60\n"))
    assert decision.severity == "block"
    assert "TIMEOUT_SECONDS" in decision.why


def test_should_block_when_value_already_named(fake_index: None) -> None:
    """A new constant whose value matches an existing one is blocked."""
    decision = constant_sprawl.check(_ctx("REQUEST_TIMEOUT = 30\n"))
    assert decision.severity == "block"
    assert "TIMEOUT_SECONDS" in decision.why


def test_should_allow_when_value_is_trivial(fake_index: None) -> None:
    """Trivial values (0, 1, -1, empty string) may legitimately repeat."""
    decision = constant_sprawl.check(_ctx("DEFAULT_INDEX = 0\nINITIAL_COUNT = 1\n"))
    assert decision.severity == "allow"


def test_should_allow_when_constant_is_truly_new(fake_index: None) -> None:
    """A constant with a fresh name and a fresh value is allowed."""
    decision = constant_sprawl.check(_ctx("MAX_RETRIES = 7\n"))
    assert decision.severity == "allow"


def test_should_block_when_string_value_collides(fake_index: None) -> None:
    """Value collision works for strings too."""
    decision = constant_sprawl.check(_ctx('USER_SECT = "shia"\n'))
    assert decision.severity == "block"
    assert "SECT_SHIA" in decision.why


def test_should_skip_non_production_paths() -> None:
    """Outside src/, the rule does not apply."""
    ctx = HookContext(
        tool_name="Write",
        file_path=Path("/repo/scripts/oneshot.py").resolve(),
        command=None,
        new_content="TIMEOUT_SECONDS = 99\n",
        old_content=None,
    )
    decision = constant_sprawl.check(ctx)
    assert decision.severity == "allow"
