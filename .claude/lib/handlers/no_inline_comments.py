"""Block code comments — intent belongs in docstrings and names, not ``#``.

Why: the project convention is self-documenting code. Comments drift out of
sync with the code they describe; docstrings and well-chosen names do not.
Both *inline* comments (``code  # note``) and *standalone* comments
(``# note`` on its own line) are blocked.

Comments are detected with :mod:`tokenize`, so a ``#`` inside a string or a
docstring is never mistaken for a comment.

Allowed (verbatim): tooling directives ``# type:``, ``# noqa``, ``# pragma``,
``# fmt:``, ``# pylint:``, ``# mypy:``, ``# pyright:``; the shebang and
``# -*-`` encoding lines; ``# ====`` / ``# ----`` section dividers; and any
line carrying a ``\\uXXXX`` escape (the Arabic transliteration maps annotate
each escape with its rendered glyph).
"""

from __future__ import annotations

import io
import re
import tokenize

from ..context import HookContext
from ..decision import Decision

HANDLER = "no_inline_comments"
RULE_ID = "DOC-011"
DOC = "docs/quality-standards.md#comments"

_DIRECTIVES = ("type:", "noqa", "pragma", "fmt:", "pylint:", "mypy:", "pyright:")
_DIVIDER = re.compile(r"#\s*[=-]+\s*$")


def _is_exempt(tok: tokenize.TokenInfo) -> bool:
    """True if this comment token is an allowed exception."""
    body = tok.string.lstrip("#").strip()
    if any(body.startswith(directive) for directive in _DIRECTIVES):
        return True
    if tok.string.startswith(("#!", "# -*-")):
        return True
    if _DIVIDER.match(tok.string):
        return True
    return "\\u" in tok.line


def check(ctx: HookContext) -> Decision:
    """Block inline and standalone code comments in Python files."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "py":
        return Decision.allow(HANDLER)
    if ctx.file_path is None:
        return Decision.allow(HANDLER)
    name = ctx.file_path.name
    if name in {"__init__.py", "conftest.py"}:
        return Decision.allow(HANDLER)
    if name.startswith("test_") or name.endswith("_test.py"):
        return Decision.allow(HANDLER)

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(ctx.new_content).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return Decision.allow(HANDLER)

    for tok in tokens:
        if tok.type != tokenize.COMMENT or _is_exempt(tok):
            continue
        inline = bool(tok.line[: tok.start[1]].strip())
        shape = "Inline" if inline else "Standalone"
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why=f"{shape} comment at line {tok.start[0]}: `{tok.string.strip()[:50]}`.",
            fix=(
                "Move the explanation into the nearest function/class docstring, or "
                "rename code so it explains itself. Directive comments (`# type:`, "
                "`# noqa`, ...) are allowed."
            ),
            doc=DOC,
        )
    return Decision.allow(HANDLER)
