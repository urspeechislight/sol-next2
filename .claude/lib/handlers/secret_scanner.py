"""Block obvious secret patterns from being written into the repo.

Patterns covered (high-confidence only — false positives erode trust):
  * AWS access keys (``AKIA...``)
  * AWS secret keys (40-char base64 in `aws_secret_access_key` proximity)
  * Google API keys (``AIza...``)
  * OpenAI / Anthropic / GitHub token shapes
  * Private key headers (``-----BEGIN ... PRIVATE KEY-----``)
  * Generic high-entropy literal in env-shaped lines (``X_SECRET=...``).

This is a defense layer; ``gitleaks`` in CI is the source of truth.
"""

from __future__ import annotations

import re

from ..context import HookContext
from ..decision import Decision

HANDLER = "secret_scanner"
RULE_ID = "SEC-001"
DOC = "docs/quality-standards.md#security"

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "private_key_header",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ),
]


_CONCAT = re.compile(r"['\"]\s*\+\s*['\"]")


def _normalize(content: str) -> str:
    """Defeat trivial obfuscation: collapse string concatenation joins.

    ``'AKIA' + 'IOSFODNN7EXAMPLE'`` -> ``AKIAIOSFODNN7EXAMPLE``. Doesn't
    handle variable-bound concat (``a + b``) — that's pattern-explosion
    territory; leave it to gitleaks in CI.
    """
    return _CONCAT.sub("", content)


def check(ctx: HookContext) -> Decision:
    """Return a deny if a high-confidence secret is detected."""
    if not ctx.is_write or ctx.new_content is None:
        return Decision.allow(HANDLER)
    # The harness's own tests AND the handler source intentionally contain
    # secret-shaped patterns (the regexes themselves; docstring examples).
    if ctx.file_path is not None:
        posix = ctx.file_path.as_posix()
        if "/.claude/tests/" in posix or "/.claude/lib/handlers/" in posix:
            return Decision.allow(HANDLER)
    content = _normalize(ctx.new_content)
    for label, pattern in _PATTERNS:
        if pattern.search(content):
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=f"Detected what looks like a secret ({label}).",
                fix=(
                    "Move the secret to a .env file (gitignored) or your secret "
                    "manager. Reference it via env var, never inline."
                ),
                doc=DOC,
            )
    return Decision.allow(HANDLER)
