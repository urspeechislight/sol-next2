"""Tests for the web_access handler.

web_access blocks fetches to deny-listed internal destinations (localhost,
link-local, *.local, *.internal) and records every other external fetch as an
advisory audit entry.
"""

from __future__ import annotations

from lib.context import HookContext
from lib.handlers import web_access


def _fetch_ctx(url: str) -> HookContext:
    return HookContext.from_payload({"tool_name": "WebFetch", "tool_input": {"url": url}})


def test_should_block_a_fetch_to_localhost() -> None:
    """A fetch to localhost is a deny-listed internal destination."""
    assert web_access.check(_fetch_ctx("http://localhost:8080/x")).severity == "block"


def test_should_block_a_fetch_to_a_local_host() -> None:
    """A *.local host is internal and blocked."""
    assert web_access.check(_fetch_ctx("https://titan.local/api")).severity == "block"


def test_should_block_a_fetch_to_a_link_local_address() -> None:
    """A 169.254.* link-local address is blocked."""
    assert web_access.check(_fetch_ctx("http://169.254.1.1/meta")).severity == "block"


def test_should_advise_a_fetch_to_a_public_host() -> None:
    """A public URL is allowed but recorded as an advisory audit entry."""
    assert web_access.check(_fetch_ctx("https://github.com/foo/bar")).severity == "advisory"


def test_should_allow_a_fetch_with_no_url() -> None:
    """No url or query in the tool input means nothing to check."""
    ctx = HookContext.from_payload({"tool_name": "WebFetch", "tool_input": {}})
    assert web_access.check(ctx).severity == "allow"
