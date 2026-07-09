"""Tests for the no_patchwork handler."""

from __future__ import annotations

from pathlib import Path

import pytest
from lib import paths
from lib.context import HookContext
from lib.handlers import no_patchwork


def _ctx(file_path: Path, content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    return repo


def _target(repo: Path, rel: str) -> Path:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


@pytest.mark.parametrize(
    "term",
    [
        "band-aid",
        "bandaid",
        "band aid",
        "stopgap",
        "stop-gap",
        "kludge",
        "kludgy",
        "duct tape",
        "duct-tape",
        "patchwork",
        "patch-work",
        "patch job",
        "quick fix",
        "quick-fix",
        "quick hack",
        "quick and dirty",
        "hacky",
        "good enough for now",
    ],
)
def test_should_block_patchwork_admission_in_src(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, term: str
) -> None:
    """Each corner-cut admission is blocked in application source, as string or comment."""
    repo = _repo(tmp_path, monkeypatch)
    target = _target(repo, "src/backend/x.py")
    assert no_patchwork.check(_ctx(target, f'"""{term}"""\nx = 1\n')).severity == "block"
    assert no_patchwork.check(_ctx(target, f"x = 1\n# {term}\n")).severity == "block"


@pytest.mark.parametrize("rel", ["frontend/src/features/x.ts", "frontend/src/lib/y.tsx"])
def test_should_block_patchwork_admission_in_frontend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rel: str
) -> None:
    """The gate covers the frontend app source too, not only backend Python."""
    repo = _repo(tmp_path, monkeypatch)
    target = _target(repo, rel)
    code = "export const clean = () => kludge();\n"
    assert no_patchwork.check(_ctx(target, code)).severity == "block"


def test_should_allow_clean_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Source with no admission vocabulary passes."""
    repo = _repo(tmp_path, monkeypatch)
    target = _target(repo, "src/backend/x.py")
    code = "def decompose(head: str) -> dict[str, str]:\n    return {'name': head}\n"
    assert no_patchwork.check(_ctx(target, code)).severity == "allow"


def test_should_allow_bare_patch_and_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bare `patch`/`rollback`/`feedback` is not an admission and must not trip."""
    repo = _repo(tmp_path, monkeypatch)
    target = _target(repo, "src/backend/x.py")
    code = "def apply_patch(rollback: bool, feedback: str) -> None:\n    return None\n"
    assert no_patchwork.check(_ctx(target, code)).severity == "allow"


@pytest.mark.parametrize("rel", ["scripts/review.py", "tests/test_x.py", "docs/x.md"])
def test_should_allow_admission_outside_application_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rel: str
) -> None:
    """scripts/, tests/, and docs/ may name the pattern they hunt, test, or explain."""
    repo = _repo(tmp_path, monkeypatch)
    target = _target(repo, rel)
    term = "stopgap"
    code = f"x = 1\n# {term} is discussed here\n"
    assert no_patchwork.check(_ctx(target, code)).severity == "allow"


def test_should_allow_non_python_data_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-source suffix under src/ is out of scope (only code files are checked)."""
    repo = _repo(tmp_path, monkeypatch)
    target = _target(repo, "src/backend/notes.json")
    term = "kludge"
    assert no_patchwork.check(_ctx(target, f'{{"note": "{term}"}}\n')).severity == "allow"
