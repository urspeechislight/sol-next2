"""Tests for the class_duplication handler."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from lib.context import HookContext
from lib.handlers import class_duplication


@pytest.fixture
def fake_index(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Replace the on-disk indexer + scope check with deterministic stubs."""

    def stub(exclude: Path | None) -> dict[str, Path]:
        return {
            "Book": Path("/repo/src/backend/models/book.py"),
            "ValidationError": Path("/repo/src/backend/core/errors.py"),
            "UserRole": Path("/repo/src/backend/auth/roles.py"),
        }

    def always_in_scope(_p: Path | None, *_segs: str) -> bool:
        return True

    monkeypatch.setattr(class_duplication, "_index_existing", stub)
    monkeypatch.setattr(class_duplication, "is_in", always_in_scope)
    yield


def _ctx(content: str, file_name: str = "routes.py") -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path(f"/repo/src/backend/api/{file_name}").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_no_classes_are_added(fake_index: None) -> None:
    """A function-only file is fine."""
    decision = class_duplication.check(_ctx("def fn() -> None:\n    pass\n"))
    assert decision.severity == "allow"


def test_should_block_when_class_name_collides(fake_index: None) -> None:
    """Re-defining an existing class name in a different file is blocked."""
    decision = class_duplication.check(_ctx("class Book:\n    title: str\n"))
    assert decision.severity == "block"
    assert "Book" in decision.why


def test_should_block_when_pydantic_model_collides(fake_index: None) -> None:
    """A Pydantic BaseModel subclass collision is still a collision."""
    decision = class_duplication.check(
        _ctx("from pydantic import BaseModel\n\nclass Book(BaseModel):\n    title: str\n")
    )
    assert decision.severity == "block"


def test_should_block_when_exception_class_collides(fake_index: None) -> None:
    """Exception class duplication is a special hazard for `except` blocks."""
    decision = class_duplication.check(_ctx("class ValidationError(Exception):\n    pass\n"))
    assert decision.severity == "block"


def test_should_block_when_enum_collides(fake_index: None) -> None:
    """Enum duplication splits the namespace of allowed values."""
    decision = class_duplication.check(
        _ctx("from enum import Enum\n\nclass UserRole(Enum):\n    ADMIN = 'admin'\n")
    )
    assert decision.severity == "block"


def test_should_allow_when_private_class_collides(fake_index: None) -> None:
    """Underscore-prefixed classes are file-private."""
    decision = class_duplication.check(_ctx("class _Book:\n    title: str\n"))
    assert decision.severity == "allow"


def test_should_allow_when_config_inner_class(fake_index: None) -> None:
    """`Config` is a Pydantic/SQLAlchemy/Django convention; exempt at module level."""
    decision = class_duplication.check(_ctx("class Config:\n    arbitrary = True\n"))
    assert decision.severity == "allow"


def test_should_skip_conftest_files(fake_index: None) -> None:
    """conftest.py intentionally redefines fixture classes."""
    decision = class_duplication.check(
        _ctx("class Book:\n    pass\n", file_name="conftest.py")
    )
    assert decision.severity == "allow"


def test_should_allow_when_class_is_truly_new(fake_index: None) -> None:
    """A class with a fresh name is allowed."""
    decision = class_duplication.check(_ctx("class Manuscript:\n    pages: list[str]\n"))
    assert decision.severity == "allow"
