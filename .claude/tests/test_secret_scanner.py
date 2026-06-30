"""Tests for the secret_scanner handler."""

from __future__ import annotations

from pathlib import Path

from lib.context import HookContext
from lib.handlers import secret_scanner


def _ctx(content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=Path("/tmp/x.py").resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_when_aws_access_key_present() -> None:
    """AWS access key shape triggers a deny."""
    decision = secret_scanner.check(_ctx("KEY = 'AKIAIOSFODNN7EXAMPLE'"))
    assert decision.severity == "block"


def test_should_block_when_private_key_header_present() -> None:
    """PEM private key header triggers a deny."""
    decision = secret_scanner.check(_ctx("-----BEGIN RSA PRIVATE KEY-----"))
    assert decision.severity == "block"


def test_should_allow_when_no_secret_pattern() -> None:
    """Innocuous code passes."""
    decision = secret_scanner.check(_ctx("x = 1 + 2"))
    assert decision.severity == "allow"
