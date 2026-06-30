#!/usr/bin/env python3
"""PreToolUse hook for Write|Edit|MultiEdit.

Runs cheap, content-only checks BEFORE the file is written. Anything that
needs the file on disk runs in the post-tool-use hook.
"""

from __future__ import annotations

import _bootstrap  # noqa: F401  # pyright: ignore[reportUnusedImport]
from lib import dispatcher
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


def main() -> None:
    """Run all PreToolUse:Write handlers in order.

    This is the CANONICAL chain — same content rules whether the session
    is on buildhost or on the laptop launchpoint. Laptop-specific scope
    enforcement (``launchpoint_scope``) lives in its own hook
    ``pre_tool_use_launchpoint.py`` which runs BEFORE this one — that
    way buildhost's harness doesn't import a handler that's meaningless to it.
    """
    dispatcher.run(
        event="PreToolUse:Write",
        handlers=[
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
        ],
    )


if __name__ == "__main__":
    main()
