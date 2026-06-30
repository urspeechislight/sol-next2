"""Tests for the bash_file_write handler."""

from __future__ import annotations

from lib.context import HookContext
from lib.handlers import bash_file_write


def _ctx(command: str) -> HookContext:
    return HookContext(
        tool_name="Bash",
        file_path=None,
        command=command,
        new_content=None,
        old_content=None,
    )


def test_should_block_when_echo_redirect_to_project() -> None:
    """`echo > foo.svelte` writes a project file via Bash."""
    assert bash_file_write.check(_ctx('echo "x" > src/frontend/x.svelte')).severity == "block"


def test_should_block_when_heredoc_to_project() -> None:
    """`cat <<EOF > foo` is denied."""
    assert bash_file_write.check(_ctx("cat <<EOF > src/x.py\nfoo\nEOF")).severity == "block"


def test_should_block_when_tee_writes_project_file() -> None:
    """`tee` writing a project file is denied."""
    assert bash_file_write.check(_ctx("echo x | tee src/x.py")).severity == "block"


def test_should_block_when_python_open_writes_project_file() -> None:
    """`python -c "open(...)"` is denied."""
    cmd = "python3 -c \"open('src/x.py', 'w').write('y')\""
    assert bash_file_write.check(_ctx(cmd)).severity == "block"


def test_should_block_when_sed_inplace_on_project_file() -> None:
    """`sed -i` on a project file is denied."""
    assert bash_file_write.check(_ctx("sed -i 's/a/b/' src/frontend/x.ts")).severity == "block"


def test_should_block_when_dd_of_to_project() -> None:
    """`dd of=...` denied."""
    assert bash_file_write.check(_ctx("dd if=/dev/zero of=src/x.bin bs=1")).severity == "block"


def test_should_block_when_curl_writes_to_project() -> None:
    """`curl ... -o src/...` denied."""
    assert (
        bash_file_write.check(_ctx("curl https://x.test -o src/frontend/x.ts")).severity == "block"
    )


def test_should_block_when_git_apply() -> None:
    """`git apply` denied."""
    assert bash_file_write.check(_ctx("git apply patch.diff")).severity == "block"


def test_should_allow_when_redirect_to_tmp() -> None:
    """Writes to /tmp/ are scratch, allowed."""
    assert bash_file_write.check(_ctx("echo x > /tmp/scratch.txt")).severity == "allow"


def test_should_allow_when_redirect_to_dev_null() -> None:
    """`> /dev/null` is allowed."""
    assert bash_file_write.check(_ctx("git status > /dev/null 2>&1")).severity == "allow"


def test_should_allow_when_no_write_construct() -> None:
    """Plain commands pass."""
    assert bash_file_write.check(_ctx("git status && ls -la")).severity == "allow"


def test_should_allow_when_stderr_redirect_only() -> None:
    """`2>&1` redirect doesn't trigger a write block."""
    assert bash_file_write.check(_ctx("git status 2>&1 | head")).severity == "allow"
