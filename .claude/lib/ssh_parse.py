"""Parse SSH-to-buildhost Bash commands into extracted (dest, content) writes.

Pure parsing helpers used by the ``ssh_remote_write`` handler. Split out so
the handler module stays under the 450-LOC hard cap and so the parsing
logic can be unit-tested independently.

Public surface:
  - ``ExtractedWrite`` — one extracted write (dest path on buildhost + content)
  - ``looks_like_buildhost_call(cmd)`` — quick yes/no on whether to parse
  - ``remote_to_local(remote_abs_path)`` — map buildhost repo path → laptop path
  - ``extract_writes(cmd)`` — the main entry point

Out of scope (best-effort only):
  - Multiple writes chained with ``&&`` in one Bash call — extract first.
  - Heavily-escaped or programmatically-generated content.
  - --no-verify on a subsequent git commit (handled by the bash hook).
"""

from __future__ import annotations

import logging
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

_log = logging.getLogger(__name__)

# Remote repo root on buildhost.
REMOTE_REPO = "/home/dev/code/sol-next2"
# Laptop-side equivalent — REPO_ROOT for the mirrored harness's handlers.
LOCAL_REPO = "/Users/me/code/sol-next2"
# Tilde forms that map to the same place.
_REMOTE_REPO_TILDE_VARIANTS: tuple[str, ...] = (
    "~/code/sol-next2",
    "$HOME/code/sol-next2",
)

# Patterns that identify "this Bash call talks to buildhost."
_buildhost_MARKERS: tuple[str, ...] = (
    "dev@buildhost",
    "dev@10.0.0.10",
    "./scripts/buildhost",
    "scripts/buildhost",
    "buildhost_key",
)

# Inside the remote command string, these substrings indicate "this is a
# write to a remote file." We extract the dest path with the regexes below.
_REMOTE_REDIRECT = re.compile(
    r"(?<![0-9&])>{1,2}\s*"
    r"(?P<q>[\"']?)(?P<target>[^\s\"'<>|&;`]+)(?P=q)"
)
_REMOTE_TEE = re.compile(
    r"\btee\b(?:\s+-[a-zA-Z]+)*\s+(?P<q>[\"']?)(?P<target>[^\s\"'<>|&;`]+)(?P=q)"
)
_REMOTE_DD_OF = re.compile(r"\bdd\b[^\n]*\bof=(?P<q>[\"']?)(?P<target>[^\s\"';|&]+)(?P=q)")

# Heredoc opener: `<<` or `<<-` with optional quoting of the tag.
_HEREDOC_OPEN = re.compile(
    r"<<(?P<dash>-?)\s*(?P<openq>[\"']?)(?P<tag>[A-Za-z_][A-Za-z0-9_]*)(?P=openq)"
)

# Stdin from a local file: `< /tmp/foo` (not `<<`, not `<&`).
_STDIN_FILE = re.compile(r"(?<![<&])<\s+(?P<q>[\"']?)(?P<src>[^\s\"'<>|&;`]+)(?P=q)")

# Upstream echo/printf pipe: `echo ... | ssh ...` or `printf ... | ssh ...`.
_UPSTREAM_PIPE = re.compile(
    r"^\s*(?P<cmd>echo|printf)\s+(?P<args>.+?)\s*\|\s*(?:ssh|scp|rsync|\./scripts/buildhost|scripts/buildhost)\b",
    re.DOTALL,
)

# scp / rsync source detection.
_SCP_RSYNC = re.compile(
    r"\b(?P<tool>scp|rsync)\b(?:\s+-[A-Za-z]+)*\s+"
    r"(?P<src>\S+)\s+"
    r"(?P<dest>\S+:\S+)"
)


@dataclass(frozen=True, slots=True)
class ExtractedWrite:
    """A single remote write extracted from a Bash command."""

    remote_dest: str
    """Absolute path on buildhost, e.g. /home/dev/code/sol-next2/src/backend/foo.py."""
    local_equivalent: Path
    """Same file mapped to its laptop-side REPO_ROOT-relative location."""
    content: str
    """The bytes that would land on buildhost."""
    source: str
    """How we extracted it: 'heredoc' / 'stdin-file' / 'pipe' / 'scp' / 'rsync' / 'unknown'."""


def looks_like_buildhost_call(cmd: str) -> bool:
    """True if the Bash command is plausibly talking to buildhost."""
    return any(m in cmd for m in _buildhost_MARKERS)


def remote_to_local(remote_abs: str) -> Path:
    """Map a /home/dev/code/sol-next2/<rel> path to its laptop equivalent."""
    rel = remote_abs[len(REMOTE_REPO):].lstrip("/")
    return Path(LOCAL_REPO) / rel


def _normalize_remote_path(raw: str) -> str | None:
    """Resolve tilde / cd-relative paths to an absolute path under REMOTE_REPO.

    Returns None if the path is not inside the repo (the handler then bows
    out — that's a write the user intends to land somewhere else on buildhost,
    not our concern).
    """
    p = raw.strip().strip("\"'")
    for tilde in _REMOTE_REPO_TILDE_VARIANTS:
        if p.startswith(tilde + "/"):
            return REMOTE_REPO + "/" + p[len(tilde) + 1:]
        if p == tilde:
            return REMOTE_REPO
    if p.startswith(REMOTE_REPO + "/") or p == REMOTE_REPO:
        return p
    # Relative path — assume the wrapper cd'd into REMOTE_REPO first
    # (./scripts/buildhost does this). Reject obvious escapes.
    if p.startswith("/"):
        return None
    if ".." in Path(p).parts:
        return None
    return REMOTE_REPO + "/" + p


def _extract_heredocs(cmd: str) -> dict[str, str]:
    """Find every heredoc in the Bash command and return {tag: body}.

    Bash heredoc syntax::

        cmd <<EOF
        body
        EOF
        cmd <<'EOF'           # quoted = no interpolation, literal
        body
        EOF
        cmd <<-EOF            # leading tabs stripped (we honor it)
        \tbody
        \tEOF
    """
    out: dict[str, str] = {}
    for opener in _HEREDOC_OPEN.finditer(cmd):
        tag = opener.group("tag")
        dash = opener.group("dash") == "-"
        after_opener = cmd[opener.end():]
        nl = after_opener.find("\n")
        if nl == -1:
            continue
        body_and_rest = after_opener[nl + 1:]
        if dash:
            closer = re.compile(r"(?m)^[ \t]*" + re.escape(tag) + r"\s*$")
        else:
            closer = re.compile(r"(?m)^" + re.escape(tag) + r"\s*$")
        end = closer.search(body_and_rest)
        if not end:
            continue
        body = body_and_rest[: end.start()]
        if dash:
            body = "\n".join(line.lstrip("\t") for line in body.splitlines())
        out[tag] = body
    return out


def _read_stdin_file(cmd: str) -> tuple[str, str] | None:
    """If the command reads stdin from a local file, return (src, content)."""
    m = _STDIN_FILE.search(cmd)
    if not m:
        return None
    src = m.group("src")
    try:
        content = Path(src).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        _log.warning("ssh_parse: cannot read stdin source %r: %s", src, e)
        return None
    return src, content


def _extract_upstream_pipe(cmd: str) -> str | None:
    """Extract content from `echo "..." | ssh ...` or `printf ...`."""
    m = _UPSTREAM_PIPE.search(cmd.strip())
    if not m:
        return None
    args = m.group("args")
    # Run `echo args` / `printf args` through bash to get the real string.
    # Safe: we don't pass user-controlled commands, just `echo`/`printf` with
    # the literal arg string the agent wrote.
    tool = m.group("cmd")
    try:
        result = subprocess.run(  # noqa: S603 — args list, no shell
            ["bash", "-c", f"{tool} {args}"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        _log.warning("ssh_parse: upstream-pipe expansion failed for %r: %s", tool, e)
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _split_into_remote_commands(cmd: str) -> Iterable[str]:
    """Yield each shell-quoted remote command embedded in an ssh/scripts/buildhost call.

    Best-effort: extract single- or double-quoted arguments that follow
    ``ssh ... buildhost`` or ``./scripts/buildhost``. Each one is a candidate
    remote command (may contain its own ``cat >`` or ``tee`` redirect).
    """
    for m in re.finditer(r"""(?P<q>['"])(?P<body>(?:\\.|(?!(?P=q)).)*)(?P=q)""", cmd):
        yield m.group("body")


def _scp_rsync_writes(cmd: str) -> Iterable[ExtractedWrite]:
    """Yield ExtractedWrite for every scp/rsync that targets buildhost's repo."""
    for m in _SCP_RSYNC.finditer(cmd):
        src = m.group("src")
        dest = m.group("dest")
        if "buildhost" not in dest:
            continue
        _, _, rpath = dest.partition(":")
        remote_abs = _normalize_remote_path(rpath)
        if remote_abs is None:
            continue
        try:
            content = Path(src).read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            _log.warning("ssh_parse: cannot read scp/rsync source %r: %s", src, e)
            content = ""
        yield ExtractedWrite(
            remote_dest=remote_abs,
            local_equivalent=remote_to_local(remote_abs),
            content=content,
            source=m.group("tool"),
        )


def _pick_content(
    heredocs: dict[str, str],
    upstream: str | None,
    stdin_file: tuple[str, str] | None,
) -> tuple[str | None, str]:
    """Choose the most likely content source for an embedded ssh write.

    Returns (content, source-label). content is None when no source matched.
    Priority: single heredoc > multi-heredoc > upstream echo/printf pipe >
    local file via < /tmp/foo.
    """
    if len(heredocs) == 1:
        return next(iter(heredocs.values())), "heredoc"
    if heredocs:
        return next(iter(heredocs.values())), "heredoc"
    if upstream is not None:
        return upstream, "pipe"
    if stdin_file is not None:
        return stdin_file[1], "stdin-file"
    return None, "unknown"


def extract_writes(cmd: str) -> list[ExtractedWrite]:
    """Pull every (dest, content) pair this Bash command would land on buildhost."""
    writes: list[ExtractedWrite] = list(_scp_rsync_writes(cmd))

    heredocs = _extract_heredocs(cmd)
    upstream = _extract_upstream_pipe(cmd)
    stdin_file = _read_stdin_file(cmd)

    for remote_cmd in _split_into_remote_commands(cmd):
        dest_match = (
            _REMOTE_REDIRECT.search(remote_cmd)
            or _REMOTE_TEE.search(remote_cmd)
            or _REMOTE_DD_OF.search(remote_cmd)
        )
        if not dest_match:
            continue
        raw_dest = dest_match.group("target")
        remote_abs = _normalize_remote_path(raw_dest)
        if remote_abs is None:
            continue
        content, source = _pick_content(heredocs, upstream, stdin_file)
        writes.append(
            ExtractedWrite(
                remote_dest=remote_abs,
                local_equivalent=remote_to_local(remote_abs),
                content=content if content is not None else "",
                source=source,
            )
        )

    return writes
