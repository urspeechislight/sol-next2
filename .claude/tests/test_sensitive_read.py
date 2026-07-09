"""Tests for the sensitive_read handler.

sensitive_read blocks reads of known secret stores (.env, private keys, ...) and
of out-of-repo system directories, so credentials never land in context; reads
inside the repo are allowed and other out-of-repo paths are advisory.
"""

from __future__ import annotations

from lib.context import HookContext
from lib.handlers import sensitive_read
from lib.paths import REPO_ROOT


def _read_ctx(path: str) -> HookContext:
    return HookContext.from_payload({"tool_name": "Read", "tool_input": {"file_path": path}})


def test_should_block_reading_a_dotenv_file() -> None:
    """A .env file is a secret store and is blocked."""
    decision = _read_ctx("/tmp/proj/.env")
    result = sensitive_read.check(decision)
    assert result.severity == "block"


def test_should_block_reading_a_dotenv_variant() -> None:
    """.env.local and similar variants are blocked too."""
    assert sensitive_read.check(_read_ctx("/tmp/proj/.env.local")).severity == "block"


def test_should_block_reading_a_private_key() -> None:
    """A private key file name is blocked."""
    assert sensitive_read.check(_read_ctx("/home/u/keys/id_rsa")).severity == "block"


def test_should_block_reading_a_system_directory() -> None:
    """Out-of-repo system paths like /etc are blocked."""
    assert sensitive_read.check(_read_ctx("/etc/passwd")).severity == "block"


def test_should_allow_reading_a_normal_repo_file() -> None:
    """An ordinary file inside the repo is fine to read."""
    assert sensitive_read.check(_read_ctx(str(REPO_ROOT / "README.md"))).severity == "allow"


def test_should_advise_reading_outside_the_repo() -> None:
    """A non-secret path outside the repo is advisory, not blocked."""
    assert sensitive_read.check(_read_ctx("/tmp/scratch/notes.txt")).severity == "advisory"
