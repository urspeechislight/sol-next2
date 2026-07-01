"""Tests for the css_duplication handler (UI-001)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from lib.context import HookContext
from lib.handlers import css_duplication


@pytest.fixture
def fake_index(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Replace the on-disk indexer + scope check with deterministic stubs."""

    def stub(exclude: Path | None) -> dict[str, Path]:
        return {
            ".metric-card": Path("/repo/frontend/src/components.css"),
            ".metric-grid": Path("/repo/frontend/src/components.css"),
            ".topbar": Path("/repo/frontend/src/shell.css"),
            ".cat-badge": Path("/repo/frontend/src/components.css"),
        }

    def always_in_scope(_p: Path | None, *_segs: str) -> bool:
        return True

    monkeypatch.setattr(css_duplication, "_index_existing", stub)
    monkeypatch.setattr(css_duplication, "is_in", always_in_scope)
    yield


def _ctx(content: str, file_name: str = "dashboard.css") -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path(f"/repo/frontend/src/{file_name}").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_allow_when_selector_is_unique(fake_index: None) -> None:
    """A fresh selector that nobody else defines is fine."""
    decision = css_duplication.check(_ctx(".pipeline-bar { background: red; }"))
    assert decision.severity == "allow"


def test_should_block_when_class_selector_collides(fake_index: None) -> None:
    """Re-defining `.metric-card` in dashboard.css after components.css is blocked."""
    decision = css_duplication.check(_ctx(".metric-card { padding: 20px; }"))
    assert decision.severity == "block"
    assert ".metric-card" in decision.why
    assert "components.css" in decision.why


def test_should_block_inside_selector_list(fake_index: None) -> None:
    """A comma-separated list expands; collision on any branch blocks."""
    decision = css_duplication.check(_ctx(".pipeline-bar, .metric-grid { gap: 8px; }"))
    assert decision.severity == "block"


def test_should_allow_when_root_redefined(fake_index: None) -> None:
    """`:root` is exempt — design-token files legitimately redefine it."""
    decision = css_duplication.check(
        _ctx(":root { --cat-clean: #4ade80; --cat-ref_number: #facc15; }")
    )
    assert decision.severity == "allow"


def test_should_allow_when_theme_scope_redefined(fake_index: None) -> None:
    """Theme-scoped token blocks (html[data-theme=...]) are exempt."""
    decision = css_duplication.check(
        _ctx('html[data-theme="dark"] { --c-bg: #000; }')
    )
    assert decision.severity == "allow"


def test_should_allow_media_query(fake_index: None) -> None:
    """`@media` at-rules are exempt from selector matching."""
    decision = css_duplication.check(
        _ctx("@media (max-width: 600px) { .x { display: none; } }")
    )
    assert decision.severity == "allow"


def test_should_allow_selector_inside_media_block(fake_index: None) -> None:
    """A `.metric-card` rule inside @media isn't a top-level redefinition."""
    decision = css_duplication.check(
        _ctx("@media (max-width: 900px) { .metric-card { padding: 8px; } }")
    )
    assert decision.severity == "allow"


def test_should_block_top_level_even_with_media_after(fake_index: None) -> None:
    """A top-level duplicate IS still caught when an @media follows."""
    decision = css_duplication.check(
        _ctx(".metric-card { padding: 8px; }\n@media (max-width: 900px) { .x { color: red; } }")
    )
    assert decision.severity == "block"
    assert ".metric-card" in decision.why


def test_should_skip_when_outside_static_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """CSS files outside frontend/src/ are not in scope."""

    def _not_in_static(_path: Path | None, *_segments: str) -> bool:
        return False

    monkeypatch.setattr(css_duplication, "is_in", _not_in_static)
    decision = css_duplication.check(
        HookContext(
            tool_name="Write",
            file_path=Path("/repo/somewhere/else.css").resolve(),
            command=None,
            new_content=".metric-card { padding: 1px; }",
            old_content=None,
        )
    )
    assert decision.severity == "allow"


def test_should_ignore_commented_selectors(fake_index: None) -> None:
    """A selector inside a /* comment */ is not a real definition."""
    decision = css_duplication.check(
        _ctx("/* .metric-card { padding: 20px; } */\n.foo { color: red; }")
    )
    assert decision.severity == "allow"


def test_should_allow_when_only_at_rules(fake_index: None) -> None:
    """A file containing only @keyframes / @media has no top-level selectors."""
    decision = css_duplication.check(
        _ctx("@keyframes spin { 0% { transform: rotate(0); } 100% { transform: rotate(360deg); } }")
    )
    assert decision.severity == "allow"
