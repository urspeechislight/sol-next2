#!/usr/bin/env python3
"""Pre-commit harness: run all PreToolUse:Write handlers over staged files.

Why: the in-session PreToolUse:Write hook only fires when the agent's
Write/Edit/MultiEdit tool call is intercepted by THIS Claude Code process.
Sessions initiated from the laptop (driving buildhost over SSH+Bash) bypass
that interception. Mirroring the handler chain into lefthook's pre-commit
makes every commit on buildhost pass the same gates regardless of where the
session ran.

Usage (from lefthook):
    python3 .claude/hooks/lint_staged.py {staged_files}

If invoked with no args, derives the list from
    git diff --cached --name-only --diff-filter=ACMR

Exits 0 on clean, 1 if any staged file has a block-level violation.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import _bootstrap  # noqa: F401  # pyright: ignore[reportUnusedImport]  — sets up sys.path so lib.* imports work
from lib.context import HookContext
from lib.decision import Decision
from lib.handlers import (
    centralization,
    class_duplication,
    constant_sprawl,
    docs_location,
    external_refs,
    fail_loud,
    file_size_cap,
    function_duplication,
    function_size_cap,
    import_boundaries,
    magic_numbers,
    no_arbitrary_values,
    no_fallback,
    no_inline_styles,
    no_print,
    no_raw_colors,
    no_silent_except,
    primitive_usage,
    secret_scanner,
    single_pyproject,
    test_naming,
    typed_python,
    variants_only,
)

# Handler chain. Order mirrors pre_tool_use_write.py exactly so the at-commit
# gate is interchangeable with the in-session gate.
HANDLERS = [
    secret_scanner.check,
    external_refs.check,
    no_raw_colors.check,
    no_arbitrary_values.check,
    no_inline_styles.check,
    primitive_usage.check,
    variants_only.check,
    import_boundaries.check,
    no_silent_except.check,
    fail_loud.check,
    no_fallback.check,
    no_print.check,
    typed_python.check,
    magic_numbers.check,
    constant_sprawl.check,
    function_duplication.check,
    class_duplication.check,
    centralization.check,
    single_pyproject.check,
    function_size_cap.check,
    file_size_cap.check,
    test_naming.check,
    docs_location.check,
]


def _staged_files_from_git() -> list[str]:
    """Return staged paths (Added/Copied/Modified/Renamed) from git index."""
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],  # noqa: S607  -- trusted git on PATH
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in out.stdout.splitlines() if line.strip()]


def _staged_content(path: str) -> str | None:
    """Return staged content for `path`; fall back to working-tree if not staged.

    The staged path is canonical for pre-commit (we evaluate exactly what's
    about to land). The working-tree fallback makes the script usable from
    argv for ad-hoc debugging on files that aren't in the index.
    """
    try:
        out = subprocess.run(  # noqa: S603  -- trusted git, path is from staged-file list, not user input
            ["git", "show", f":{path}"],  # noqa: S607  -- trusted git on PATH
            capture_output=True,
            check=True,
        )
        return out.stdout.decode("utf-8")
    except (subprocess.CalledProcessError, UnicodeDecodeError):
        try:
            return Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None


def _check_one(file_path: str) -> tuple[list[Decision], list[Decision]]:
    """Return (advisories, blocks) produced by the handler chain for one file."""
    content = _staged_content(file_path)
    if content is None:
        return [], []
    abs_path = Path(file_path).resolve()
    ctx = HookContext(
        tool_name="Write",
        file_path=abs_path,
        command=None,
        new_content=content,
        old_content=None,
    )
    advisories: list[Decision] = []
    blocks: list[Decision] = []
    for handler in HANDLERS:
        verdict = handler(ctx)
        if verdict.is_block():
            blocks.append(verdict)
            break  # first deny wins, matching dispatcher.run semantics
        if verdict.is_advisory():
            advisories.append(verdict)
    return advisories, blocks


def _emit_file_report(file_path: str, advisories: list[Decision], blocks: list[Decision]) -> None:
    """Write a per-file decision summary to stderr."""
    sys.stderr.write(f"\n[{file_path}]\n")
    for a in advisories:
        sys.stderr.write(f"  WARN  {a.handler} ({a.rule_id}): {a.why}\n")
        if a.fix:
            sys.stderr.write(f"        fix: {a.fix}\n")
    for b in blocks:
        sys.stderr.write(f"  BLOCK {b.handler} ({b.rule_id}): {b.why}\n")
        sys.stderr.write(f"        fix: {b.fix}\n")
        if b.doc:
            sys.stderr.write(f"        doc: {b.doc}\n")


def main() -> None:
    """Run the handler chain over staged (or argv-provided) files."""
    files = sys.argv[1:] or _staged_files_from_git()
    if not files:
        sys.exit(0)

    any_block = False
    for f in files:
        advisories, blocks = _check_one(f)
        if not (advisories or blocks):
            continue
        _emit_file_report(f, advisories, blocks)
        if blocks:
            any_block = True

    if any_block:
        sys.stderr.write(
            "\nharness-rules pre-commit gate failed. Fix the issues above and "
            "re-stage. These are the same rules the in-session "
            "PreToolUse:Write hook enforces.\n"
        )
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
