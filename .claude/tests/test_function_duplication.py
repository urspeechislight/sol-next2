"""Tests for the function_duplication handler (DRY-001 name + DRY-003 body)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from lib import paths
from lib.context import HookContext
from lib.handlers import function_duplication

NameIndex = dict[str, Path]
BodyIndex = dict[str, tuple[str, Path]]

# A 3-statement body — above the body-fingerprint threshold.
_SAMPLE = "def original(s):\n    x = s.strip()\n    y = x.lower()\n    return y\n"


def _ctx(content: str, file_name: str = "routes.py") -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path(f"/repo/src/backend/api/{file_name}").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def _always_in_scope(_path: Path | None, *_segments: str) -> bool:
    return True


def _stub_index(
    monkeypatch: pytest.MonkeyPatch, by_name: NameIndex, by_body: BodyIndex
) -> None:
    """Stub the on-disk indexer + scope check with deterministic values."""

    def stub(_exclude: Path | None) -> tuple[NameIndex, BodyIndex]:
        return by_name, by_body

    monkeypatch.setattr(function_duplication, "_index_existing", stub)
    monkeypatch.setattr(function_duplication, "is_in", _always_in_scope)


def _real_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A real temp repo so the genuine indexer (glob + AST) runs end to end."""
    repo = tmp_path / "repo"
    (repo / "src" / "backend").mkdir(parents=True)
    monkeypatch.setattr(function_duplication, "REPO_ROOT", repo)
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    return repo


def _write_ctx(repo: Path, rel: str, content: str) -> HookContext:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    return HookContext(
        tool_name="Write",
        file_path=target.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


@pytest.fixture
def fake_index(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Name index with two known functions; empty body index."""
    _stub_index(
        monkeypatch,
        {
            "normalize_arabic": Path("/repo/src/backend/utils/text.py"),
            "load_config": Path("/repo/src/backend/core/config.py"),
        },
        {},
    )
    yield


# ---- DRY-001: name collisions -------------------------------------------------


def test_should_allow_when_no_functions_are_added(fake_index: None) -> None:
    """A constant-only file is fine."""
    assert function_duplication.check(_ctx("X = 1\n")).severity == "allow"


def test_should_block_when_public_function_name_collides(fake_index: None) -> None:
    """Re-defining an existing public function in a different file is blocked."""
    decision = function_duplication.check(_ctx("def normalize_arabic(s: str) -> str:\n    return s\n"))
    assert decision.severity == "block"
    assert "normalize_arabic" in decision.why


def test_should_allow_when_private_function_collides(fake_index: None) -> None:
    """Underscore-prefixed functions are file-private and may legitimately repeat."""
    decision = function_duplication.check(_ctx("def _normalize_arabic(s: str) -> str:\n    return s\n"))
    assert decision.severity == "allow"


def test_should_allow_when_main_is_redefined(fake_index: None) -> None:
    """`main` is a conventional entry-point name and is exempt."""
    assert function_duplication.check(_ctx("def main() -> None:\n    pass\n")).severity == "allow"


def test_should_allow_when_test_function_collides(fake_index: None) -> None:
    """`test_*` functions are pytest discovery names; collisions are expected."""
    decision = function_duplication.check(_ctx("def test_should_pass() -> None:\n    pass\n"))
    assert decision.severity == "allow"


def test_should_skip_conftest_files(fake_index: None) -> None:
    """Conftest files intentionally define same-named fixtures across dirs."""
    decision = function_duplication.check(
        _ctx("def normalize_arabic(s: str) -> str:\n    return s\n", file_name="conftest.py")
    )
    assert decision.severity == "allow"


def test_should_skip_non_production_paths() -> None:
    """Outside src/, the rule does not apply."""
    ctx = HookContext(
        tool_name="Write",
        file_path=Path("/repo/scripts/oneshot.py").resolve(),
        command=None,
        new_content="def normalize_arabic(s: str) -> str:\n    return s\n",
        old_content=None,
    )
    assert function_duplication.check(ctx).severity == "allow"


def test_should_allow_when_function_is_truly_new(fake_index: None) -> None:
    """A function with a fresh name is allowed."""
    decision = function_duplication.check(_ctx("def render_isnad(items: list[str]) -> str:\n    return ''\n"))
    assert decision.severity == "allow"


# ---- DRY-003: body collisions under a different name (real indexer) -----------


def test_should_block_body_duplicate_under_different_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A copy-paste body under a new name is blocked even when the name is fresh."""
    repo = _real_repo(tmp_path, monkeypatch)
    (repo / "src/backend/text.py").write_text(_SAMPLE)
    renamed = "def renamed_copy(s):\n    x = s.strip()\n    y = x.lower()\n    return y\n"
    decision = function_duplication.check(_write_ctx(repo, "src/backend/api/routes.py", renamed))
    assert decision.severity == "block"
    assert decision.rule_id == "DRY-003"
    assert "original" in decision.why


def test_should_ignore_docstring_when_matching_bodies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Adding a docstring to the copy does not evade the body match."""
    repo = _real_repo(tmp_path, monkeypatch)
    (repo / "src/backend/text.py").write_text(_SAMPLE)
    with_doc = 'def copy(s):\n    "doc"\n    x = s.strip()\n    y = x.lower()\n    return y\n'
    decision = function_duplication.check(_write_ctx(repo, "src/backend/api/routes.py", with_doc))
    assert decision.severity == "block"


def test_should_allow_when_bodies_differ(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A structurally different body (different call) is not a duplicate."""
    repo = _real_repo(tmp_path, monkeypatch)
    (repo / "src/backend/text.py").write_text(_SAMPLE)
    different = "def other(s):\n    x = s.strip()\n    y = x.upper()\n    return y\n"
    decision = function_duplication.check(_write_ctx(repo, "src/backend/api/routes.py", different))
    assert decision.severity == "allow"


def test_should_allow_trivial_identical_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One-statement bodies are below the threshold and never count as body-dupes."""
    repo = _real_repo(tmp_path, monkeypatch)
    (repo / "src/backend/text.py").write_text("def a(s):\n    return s.strip()\n")
    decision = function_duplication.check(
        _write_ctx(repo, "src/backend/api/routes.py", "def b(s):\n    return s.strip()\n")
    )
    assert decision.severity == "allow"
