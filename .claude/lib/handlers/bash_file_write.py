"""Block Bash commands that write project files, bypassing the Write hook.

Why: ``echo > foo``, ``cat <<EOF > foo``, ``tee``, ``sed -i``, ``dd of=``,
``python -c "open()"``, ``git apply``, ``cp``, ``mv``, ``curl -o``, etc. all
write files but never reach the Write/Edit handlers. That defeats every
SSOT/quality rule. We therefore intercept these patterns at the Bash hook
and force the agent to use the Write/Edit tool when the target is inside the
project tree.

Writes to clearly-safe paths (``/tmp/``, ``/dev/null``, ``~/.cache/``,
``/var/tmp/``, ``/dev/stdout``) remain allowed for diagnostics.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..context import HookContext
from ..decision import Decision

HANDLER = "bash_file_write"
RULE_ID = "BASH-100"
DOC = "docs/quality-standards.md#bash-file-writes"

# Paths that are always safe to write to from Bash (diagnostics, scratch).
_SAFE_PREFIXES: tuple[str, ...] = (
    "/tmp/",  # noqa: S108  -- this is a safe-prefix allowlist, not a file op
    "/var/tmp/",  # noqa: S108  -- safe-prefix allowlist
    "/dev/null",
    "/dev/stdout",
    "/dev/stderr",
    "~/.cache/",
    "/private/tmp/",  # macOS
    "$HOME/.cache/",
    "/proc/",
)

# Patterns where (group 1) captures the write target.
_REDIRECT = re.compile(
    # > or >> not preceded by digit/&  (avoids `2>&1`, `9>file`)
    r"(?<![0-9&])>{1,2}\s*"
    # optional quote, capture path until shell metachar
    r'(?P<q>["\']?)(?P<target>[^\s"\'<>|&;`]+)(?P=q)'
)
_TEE = re.compile(r"\btee\b(?:\s+-[a-zA-Z]+)*\s+(?P<q>[\"']?)(?P<target>[^\s\"'<>|&;`]+)(?P=q)")
_DD_OF = re.compile(r"\bdd\b[^\n]*\bof=(?P<q>[\"']?)(?P<target>[^\s\"';|&]+)(?P=q)")
_SED_INPLACE = re.compile(r"\bsed\b[^\n]*\s-i\b")
_PERL_INPLACE = re.compile(r"\bperl\b[^\n]*\s-i\b")
_PYTHON_OPEN = re.compile(r"\b(?:python3?|py)\b[^\n]*-c\s+[\"'].*\bopen\s*\(\s*[\"']([^\"']+)")
_NODE_WRITE = re.compile(r"\bnode\b[^\n]*-e\s+[\"'].*write(?:File|FileSync)\s*\(\s*[\"']([^\"']+)")
_GIT_APPLY = re.compile(r"\bgit\s+apply\b")
_CP_MV = re.compile(
    r"\b(?:cp|mv)\b(?:\s+-[a-zA-Z]+)*\s+\S+\s+(?P<q>[\"']?)(?P<target>[^\s\"'<>|&;`]+)(?P=q)\s*$",
    re.MULTILINE,
)
_CURL_OUT = re.compile(
    r"\bcurl\b[^\n]*\s(?:-o|--output)\s+(?P<q>[\"']?)(?P<target>[^\s\"';|&]+)(?P=q)"
)
_WGET_OUT = re.compile(
    r"\bwget\b[^\n]*\s(?:-O|--output-document)\s+(?P<q>[\"']?)(?P<target>[^\s\"';|&]+)(?P=q)"
)


def _is_safe_target(target: str) -> bool:
    """True if writing here is harmless (scratch / null / cache)."""
    target = target.strip()
    return any(target.startswith(p) for p in _SAFE_PREFIXES)


def _yield_targets(cmd: str) -> Iterable[tuple[str, str]]:
    """Yield (rule_label, target_path) for every write the command performs."""
    for label, pat in [
        ("redirect", _REDIRECT),
        ("tee", _TEE),
        ("dd_of", _DD_OF),
        ("python_open", _PYTHON_OPEN),
        ("node_write", _NODE_WRITE),
        ("cp_or_mv", _CP_MV),
        ("curl_out", _CURL_OUT),
        ("wget_out", _WGET_OUT),
    ]:
        for match in pat.finditer(cmd):
            target = match.group("target") if "target" in pat.groupindex else match.group(1)
            yield label, target


def check(ctx: HookContext) -> Decision:
    """Return a deny when Bash writes a non-scratch path."""
    if not ctx.is_bash or ctx.command is None:
        return Decision.allow(HANDLER)
    cmd = ctx.command

    # In-place editors target an existing file by name; check the command
    # for a path argument that isn't safe.
    if _SED_INPLACE.search(cmd) or _PERL_INPLACE.search(cmd):
        # Find any path-shaped argument; if all are safe, allow.
        args = re.findall(r"\s(/[\w./-]+|[\w./-]+\.[\w]+)\b", cmd)
        if any(not _is_safe_target(a) for a in args):
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why="In-place editor (sed -i / perl -i) targeting a project file.",
                fix="Use the Edit tool so the harness can validate the result.",
                doc=DOC,
            )

    if _GIT_APPLY.search(cmd):
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why="`git apply` writes patched files outside the Write/Edit pipeline.",
            fix=(
                "Apply the change with the Write or Edit tool so the harness "
                "validates the resulting content."
            ),
            doc=DOC,
        )

    for label, target in _yield_targets(cmd):
        if _is_safe_target(target):
            continue
        return Decision.deny(
            handler=HANDLER,
            rule_id=RULE_ID,
            why=(
                f"Bash file write detected ({label} → {target!r}). Writes that "
                "land in the project tree must go through the Write/Edit tool "
                "so harness rules apply."
            ),
            fix=(
                "Use the Write or Edit tool. If you genuinely need a Bash write "
                "to a scratch path, target /tmp/ or /var/tmp/."
            ),
            doc=DOC,
        )

    return Decision.allow(HANDLER)
