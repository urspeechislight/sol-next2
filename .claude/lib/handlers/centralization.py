"""Centralization rules: "this pattern lives only in these files."

Why: many SSOT bugs aren't about *names* (covered by ``constant_sprawl``,
``function_duplication``, ``class_duplication``) but about *locations* —
``os.getenv`` appearing in 20 files instead of a single settings module,
raw SQL strings sprinkled across the call sites instead of a repository
layer, route decorators scattered outside the API module. The fix shape
is the same for all of these: keep one home for the pattern, force
imports.

This handler reads ``.claude/policies/centralization.yaml`` and applies
every rule in it. Each rule says "pattern X may only appear in glob list
Y; block elsewhere." Adding a rule is YAML, not Python.

Two pattern kinds are supported:

  * ``regex`` — a Python regex matched against the source after stripping
    comments. Use for string-literal patterns (SQL, HTTP codes, route
    decorators).
  * ``ast``  — a qualified name (``os.getenv``, ``re.compile``) detected
    via AST walk. Use when the regex would be brittle.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, cast

import yaml

from ..context import HookContext
from ..decision import Decision
from ..paths import REPO_ROOT, relpath

_log = logging.getLogger(__name__)

HANDLER = "centralization"
DOC = "docs/quality-standards.md#ssot-dry"
POLICY_FILE = REPO_ROOT / ".claude" / "policies" / "centralization.yaml"

# Patterns we strip from source before regex-matching so a comment that
# mentions SELECT won't trigger the SQL rule. Covers Python (# and triple-
# quoted strings) and JS/TS (// and /* */).
_PY_LINE_COMMENT = re.compile(r"#[^\n]*")
_JS_LINE_COMMENT = re.compile(r"//[^\n]*")
_PY_BLOCK_STRING = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'')
_JS_BLOCK_COMMENT = re.compile(r"/\*[\s\S]*?\*/")
_HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")


Kind = Literal["regex", "ast"]


@dataclass(frozen=True, slots=True)
class Rule:
    """One centralization rule loaded from the policy YAML."""

    rule_id: str
    description: str
    kind: Kind
    pattern: re.Pattern[str] | None
    ast_match: tuple[str, ...]
    suffixes: frozenset[str]
    allowed_in: tuple[str, ...]
    fix: str


def _matches_glob(path_rel: str, glob: str) -> bool:
    """fnmatch-style glob match, with ``**`` supported."""
    return _glob_to_regex(glob).fullmatch(path_rel) is not None


@lru_cache(maxsize=256)
def _glob_to_regex(glob: str) -> re.Pattern[str]:
    """Translate a glob like ``src/**/*.py`` into a regex."""
    # Escape regex metas, then re-introduce glob semantics
    out: list[str] = []
    i = 0
    while i < len(glob):
        c = glob[i]
        if c == "*":
            if i + 1 < len(glob) and glob[i + 1] == "*":
                out.append(".*")
                i += 2
                if i < len(glob) and glob[i] == "/":
                    i += 1
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c in ".+()[]{}|^$\\":
            out.append(re.escape(c))
        else:
            out.append(c)
        i += 1
    return re.compile("".join(out))


def _load_rules() -> list[Rule]:
    """Parse ``centralization.yaml`` into Rule objects. Raises on malformed YAML."""
    if not POLICY_FILE.exists():
        return []
    raw_any: Any = yaml.safe_load(POLICY_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw_any, dict):
        return []
    raw = cast(dict[str, Any], raw_any)
    rules_raw_any: Any = raw.get("rules") or []
    if not isinstance(rules_raw_any, list):
        return []
    rules_raw = cast(list[Any], rules_raw_any)
    rules: list[Rule] = []
    for r_any in rules_raw:
        if not isinstance(r_any, dict):
            continue
        r = cast(dict[str, Any], r_any)
        kind_raw = r.get("kind")
        if kind_raw not in {"regex", "ast"}:
            continue
        kind: Kind = cast(Kind, kind_raw)
        pattern_str = r.get("pattern") if kind == "regex" else None
        pattern = re.compile(str(pattern_str)) if isinstance(pattern_str, str) else None
        ast_match_list = r.get("ast_match") or []
        ast_match = tuple(str(x) for x in ast_match_list) if isinstance(ast_match_list, list) else ()
        suffixes_list = r.get("suffixes") or []
        suffixes = (
            frozenset(str(x) for x in suffixes_list) if isinstance(suffixes_list, list) else frozenset()
        )
        allowed_list = r.get("allowed_in") or []
        allowed_in = tuple(str(x) for x in allowed_list) if isinstance(allowed_list, list) else ()
        rules.append(
            Rule(
                rule_id=str(r.get("id", "CENTRAL-???")),
                description=str(r.get("description", "")),
                kind=kind,
                pattern=pattern,
                ast_match=ast_match,
                suffixes=suffixes,
                allowed_in=allowed_in,
                fix=str(r.get("fix", "")),
            )
        )
    return rules


def _strip_for_regex(content: str) -> str:
    """Drop block strings/comments and line comments — covers Py, JS, HTML."""
    content = _PY_BLOCK_STRING.sub("", content)
    content = _JS_BLOCK_COMMENT.sub("", content)
    content = _HTML_COMMENT.sub("", content)
    content = _PY_LINE_COMMENT.sub("", content)
    content = _JS_LINE_COMMENT.sub("", content)
    return content


def _qualified_calls(tree: ast.Module) -> Iterable[tuple[str, int]]:
    """Yield (dotted_name, line) for every Call in `tree`."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _qualified_name(node.func)
            if name:
                yield name, node.lineno


def _qualified_name(node: ast.expr) -> str:
    """Render a Call's `func` as a dotted name like `os.environ.get` or empty."""
    parts: list[str] = []
    cur: ast.expr = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def _path_allowed(rule: Rule, path: Path) -> bool:
    """True if `path` (relative to repo root) matches any glob in rule.allowed_in."""
    try:
        rel = path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return True  # path outside repo — don't apply rule
    return any(_matches_glob(rel, g) for g in rule.allowed_in)


def _check_regex(rule: Rule, content: str, ctx_path: Path) -> Decision | None:
    """Apply a `regex`-kind rule. Return a Decision or None to continue."""
    if rule.pattern is None:
        return None
    stripped = _strip_for_regex(content)
    match = rule.pattern.search(stripped)
    if not match:
        return None
    if _path_allowed(rule, ctx_path):
        return None
    snippet = match.group(0)
    return Decision.deny(
        handler=HANDLER,
        rule_id=rule.rule_id,
        why=(
            f"{rule.description} Pattern `{snippet[:60]}...` found in "
            f"`{relpath(ctx_path)}` — not in the allowed locations."
        ),
        fix=rule.fix,
        doc=DOC,
    )


def _check_ast(rule: Rule, content: str, ctx_path: Path) -> Decision | None:
    """Apply an `ast`-kind rule. Return a Decision or None to continue."""
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        _log.debug("centralization: ast.parse failed on %s: %s", relpath(ctx_path), e)
        return None
    for name, lineno in _qualified_calls(tree):
        for target in rule.ast_match:
            if name == target or name.endswith("." + target):
                if _path_allowed(rule, ctx_path):
                    return None
                return Decision.deny(
                    handler=HANDLER,
                    rule_id=rule.rule_id,
                    why=(
                        f"{rule.description} Call to `{target}` at line {lineno} of "
                        f"`{relpath(ctx_path)}` — not in the allowed locations."
                    ),
                    fix=rule.fix,
                    doc=DOC,
                )
    return None


def check(ctx: HookContext) -> Decision:
    """Apply every rule in centralization.yaml to the new content."""
    if not ctx.is_write or ctx.new_content is None or ctx.file_path is None:
        return Decision.allow(HANDLER)

    for rule in _load_rules():
        if rule.suffixes and ctx.suffix not in rule.suffixes:
            continue
        if rule.kind == "regex":
            verdict = _check_regex(rule, ctx.new_content, ctx.file_path)
        else:
            verdict = _check_ast(rule, ctx.new_content, ctx.file_path)
        if verdict is not None:
            return verdict
    return Decision.allow(HANDLER)
