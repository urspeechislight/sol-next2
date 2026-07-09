"""Tests that quality.yaml is a true mirror of the handlers and that every DOC
anchor a handler links to resolves in the generated docs.

The policy registry (.claude/policies/quality.yaml) and the docs/ standards pages
are both projections of the enforcement code. These lock in that projection so it
cannot silently drift: a new write-chain handler with no rule entry, a rule whose
handler was renamed, a duplicate id, or a block message pointing at a missing doc
anchor all fail here.
"""

from __future__ import annotations

import ast
import re

import yaml

from lib.paths import REPO_ROOT

_CLAUDE = REPO_ROOT / ".claude"
_QUALITY_YAML = _CLAUDE / "policies" / "quality.yaml"
_WRITE_HOOK = _CLAUDE / "hooks" / "pre_tool_use_write.py"
_HANDLERS_DIR = _CLAUDE / "lib" / "handlers"
_DOC_REF = re.compile(r"docs/[a-z-]+\.md#[a-z-]+")


def _rules() -> list[dict[str, object]]:
    return yaml.safe_load(_QUALITY_YAML.read_text(encoding="utf-8"))["rules"]


def _write_chain_handlers() -> set[str]:
    tree = ast.parse(_WRITE_HOOK.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "lib.handlers":
            return {alias.name for alias in node.names}
    raise AssertionError("no `from lib.handlers import ...` in the write hook")


def _referenced_doc_anchors() -> set[str]:
    refs: set[str] = set()
    for rule in _rules():
        doc = rule.get("doc")
        if isinstance(doc, str):
            refs.add(doc)
    for path in _HANDLERS_DIR.glob("*.py"):
        refs.update(_DOC_REF.findall(path.read_text(encoding="utf-8")))
    return refs


def test_should_give_every_write_chain_handler_a_rule_entry() -> None:
    """The mirror is complete: no enforcing handler is missing from quality.yaml."""
    listed = {str(rule["handler"]) for rule in _rules()}
    missing = _write_chain_handlers() - listed
    assert not missing, f"write-chain handlers with no quality.yaml rule: {sorted(missing)}"


def test_should_bind_every_rule_to_an_existing_handler_module() -> None:
    """Every rule names a handler that exists on disk."""
    for rule in _rules():
        handler = str(rule["handler"])
        assert (_HANDLERS_DIR / f"{handler}.py").exists(), f"unknown handler: {handler}"


def test_should_give_every_rule_a_unique_id() -> None:
    """Rule ids are unique, so a block message maps to exactly one rule."""
    ids = [str(rule["id"]) for rule in _rules()]
    duplicates = sorted(i for i in set(ids) if ids.count(i) > 1)
    assert not duplicates, f"duplicate rule ids: {duplicates}"


def test_should_resolve_every_referenced_doc_anchor() -> None:
    """Every doc anchor a rule or handler links to exists as an id in its file."""
    for ref in sorted(_referenced_doc_anchors()):
        rel, anchor = ref.split("#", 1)
        doc = REPO_ROOT / rel
        assert doc.exists(), f"missing doc file for {ref}"
        assert f'id="{anchor}"' in doc.read_text(encoding="utf-8"), f"missing anchor for {ref}"
