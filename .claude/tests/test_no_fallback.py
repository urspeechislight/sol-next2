"""Tests for the no_fallback handler.

no_fallback is the strict sibling of fail_loud and a blocking write-chain gate:
it rejects the banned word, a Python `except` that does not re-raise, and a
JS/TS `catch` that does not re-throw, in src/ and scripts/ only.
"""

from __future__ import annotations

from lib.context import HookContext
from lib.handlers import no_fallback
from lib.paths import REPO_ROOT


def _ctx(content: str, rel: str = "src/backend/_probe.py") -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=(REPO_ROOT / rel).resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_the_word_fallback_in_source() -> None:
    """The word names the banned pattern, so it is blocked in src/."""
    decision = no_fallback.check(_ctx('label = "fallback"\n'))
    assert decision.severity == "block"
    assert "fallback" in decision.why.lower()


def test_should_block_inflected_fall_back_forms() -> None:
    """`fall back` and its inflections trip the same rule."""
    assert no_fallback.check(_ctx('label = "fall back"\n')).severity == "block"
    assert no_fallback.check(_ctx('label = "falling back"\n')).severity == "block"


def test_should_allow_words_that_only_resemble_the_ban() -> None:
    """Whole-word anchored, so rollback / feedback / snowfall do not trip."""
    assert no_fallback.check(_ctx('label = "rollback feedback snowfall"\n')).severity == "allow"


def test_should_block_python_except_without_raise() -> None:
    """A caught exception that does not propagate is a silent recovery path."""
    code = "try:\n    parse()\nexcept ValueError:\n    log('bad')\n"
    decision = no_fallback.check(_ctx(code))
    assert decision.severity == "block"
    assert "except" in decision.why


def test_should_allow_python_except_that_raises() -> None:
    """Re-raising, even wrapped, propagates the failure, so it is allowed."""
    code = "try:\n    parse()\nexcept ValueError as e:\n    raise RuntimeError('x') from e\n"
    assert no_fallback.check(_ctx(code)).severity == "allow"


def test_should_block_js_catch_without_throw() -> None:
    """A catch that swallows the error is blocked in a .ts source file."""
    code = "try {\n  parse();\n} catch (e) {\n  console.log(e);\n}\n"
    assert no_fallback.check(_ctx(code, rel="src/_probe.ts")).severity == "block"


def test_should_allow_js_catch_that_throws() -> None:
    """A catch that re-throws propagates the failure."""
    code = "try {\n  parse();\n} catch (e) {\n  throw new Error('x');\n}\n"
    assert no_fallback.check(_ctx(code, rel="src/_probe.ts")).severity == "allow"


def test_should_exempt_tests_and_harness_paths() -> None:
    """tests/, .claude/, and docs/ must be able to name the banned pattern."""
    code = 'label = "fallback"\n'
    assert no_fallback.check(_ctx(code, rel="tests/_probe.py")).severity == "allow"
    assert no_fallback.check(_ctx(code, rel=".claude/_probe.py")).severity == "allow"
    assert no_fallback.check(_ctx(code, rel="docs/_probe.py")).severity == "allow"


def test_should_ignore_non_source_paths_and_suffixes() -> None:
    """Out-of-scope prefixes and non-code suffixes are not checked."""
    code = 'label = "fallback"\n'
    assert no_fallback.check(_ctx(code, rel="config/_probe.py")).severity == "allow"
    assert no_fallback.check(_ctx(code, rel="src/notes.md")).severity == "allow"
