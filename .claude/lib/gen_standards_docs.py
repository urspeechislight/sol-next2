"""Generate the standards docs under docs/ from the harness policy and handlers.

Every block message a handler emits carries a DOC anchor such as
``docs/quality-standards.md#fail-fast``. Those docs are not written by hand: they
are a projection of the enforcement code, so they cannot drift from it. This
script reads ``.claude/policies/quality.yaml`` (the reviewable rule registry) and
the ``DOC`` / ``RULE_ID`` / docstring of every handler under
``.claude/lib/handlers/``, groups the rules by their target doc file and anchor,
and writes one anchored section per anchor so every referenced link resolves.

Run it via ``pnpm docs:standards``; ``pnpm docs:standards:check`` regenerates and
fails on any diff, so CI keeps the docs in sync with the code.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml

_LIB_DIR = Path(__file__).resolve().parent
_HANDLERS_DIR = _LIB_DIR / "handlers"
_QUALITY_YAML = _LIB_DIR.parent / "policies" / "quality.yaml"
_DOCS_DIR = _LIB_DIR.parents[1] / "docs"

_FILE_TITLES: dict[str, str] = {
    "quality-standards.md": "Quality Standards",
    "design-system.md": "Design System",
    "foundation.md": "Foundation",
    "repo-layout.md": "Repository Layout",
}
_ACRONYMS = frozenset({"ssot", "dry", "ui", "http", "css", "js", "ts", "loc", "sql"})
_BANNER = (
    "<!-- GENERATED from .claude/policies/quality.yaml and the handler DOC anchors "
    "by .claude/lib/gen_standards_docs.py. Do not edit by hand; run `pnpm "
    "docs:standards`. -->"
)


@dataclass(frozen=True)
class Card:
    """One rule rendered under a doc anchor."""

    rule_id: str
    handler: str
    severity: str
    summary: str
    rationale: str


def _flatten(text: str) -> str:
    """Collapse a YAML block scalar or docstring paragraph to one line."""
    return " ".join(str(text).split())


def _split_doc(doc: str) -> tuple[str, str]:
    """Split ``docs/<file>#<anchor>`` into its bare filename and anchor."""
    path, anchor = doc.split("#", 1)
    return path.removeprefix("docs/"), anchor


def _anchor_title(anchor: str) -> str:
    """Human title for an anchor slug, upcasing known acronyms and rendering the
    double-dash convention (``imports--boundaries``) as an ampersand."""
    words = anchor.replace("--", " & ").replace("-", " ").split()
    rendered = [w.upper() if w in _ACRONYMS else w.capitalize() for w in words]
    return " ".join(rendered)


def _first_paragraph(docstring: str | None) -> str:
    """The first blank-line-delimited paragraph of a module docstring."""
    if not docstring:
        return ""
    return _flatten(docstring.strip().split("\n\n", 1)[0])


def _module_meta(path: Path) -> dict[str, object]:
    """Extract ``handler``, rule ids, ``DOC``, and the lead docstring paragraph
    from a handler module without importing it."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    consts: dict[str, str] = {}
    rule_ids: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not isinstance(node.value, ast.Constant):
            continue
        value = node.value.value
        if not isinstance(value, str):
            continue
        consts[target.id] = value
        if target.id.startswith("RULE_ID"):
            rule_ids.append(value)
    return {
        "handler": consts.get("HANDLER", path.stem),
        "rule_ids": rule_ids,
        "doc": consts.get("DOC"),
        "summary": _first_paragraph(ast.get_docstring(tree)),
    }


def _load_yaml_rules() -> list[dict[str, object]]:
    """The rule list from the reviewable policy registry."""
    data = yaml.safe_load(_QUALITY_YAML.read_text(encoding="utf-8"))
    return data["rules"]


def _collect() -> dict[str, dict[str, list[Card]]]:
    """Group every rule by its doc file and anchor.

    quality.yaml rules supply the rich summary and rationale; handler DOC anchors
    with no yaml rule (e.g. the bash-safety handlers) are filled from the handler
    docstring so every referenced anchor still gets a section.
    """
    by_file: dict[str, dict[str, list[Card]]] = defaultdict(lambda: defaultdict(list))
    seen: set[tuple[str, str, str]] = set()
    for rule in _load_yaml_rules():
        doc = rule.get("doc")
        if not isinstance(doc, str):
            continue
        file, anchor = _split_doc(doc)
        handler = str(rule["handler"])
        by_file[file][anchor].append(
            Card(
                rule_id=str(rule["id"]),
                handler=handler,
                severity=str(rule.get("severity", "")),
                summary=_flatten(str(rule.get("summary", ""))),
                rationale=_flatten(str(rule.get("rationale", ""))),
            )
        )
        seen.add((file, anchor, handler))
    for path in sorted(_HANDLERS_DIR.glob("*.py")):
        meta = _module_meta(path)
        doc = meta["doc"]
        if not isinstance(doc, str):
            continue
        file, anchor = _split_doc(doc)
        handler = str(meta["handler"])
        if (file, anchor, handler) in seen:
            continue
        rule_ids = meta["rule_ids"]
        rule_id = rule_ids[0] if isinstance(rule_ids, list) and rule_ids else handler.upper()
        by_file[file][anchor].append(
            Card(
                rule_id=str(rule_id),
                handler=handler,
                severity="block",
                summary=str(meta["summary"]),
                rationale="",
            )
        )
        seen.add((file, anchor, handler))
    return by_file


def _render(filename: str, anchors: dict[str, list[Card]]) -> str:
    """Render one doc file: a banner, a title, and an anchored section per anchor."""
    title = _FILE_TITLES[filename]
    lines: list[str] = [
        _BANNER,
        "",
        f"# {title}",
        "",
        "Enforced by the harness; see the named handler under "
        "`.claude/lib/handlers/` for the exact check.",
        "",
    ]
    for anchor in sorted(anchors):
        lines += [f'<a id="{anchor}"></a>', "", f"## {_anchor_title(anchor)}", ""]
        for card in sorted(anchors[anchor], key=lambda c: c.rule_id):
            severity = f", {card.severity}" if card.severity else ""
            lines.append(f"- **{card.rule_id}** (`{card.handler}`{severity}) — {card.summary}")
            if card.rationale:
                lines.append(f"  _{card.rationale}_")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    """Write every standards doc from the current policy and handlers."""
    by_file = _collect()
    unknown = set(by_file) - set(_FILE_TITLES)
    if unknown:
        raise ValueError(f"DOC anchors reference undeclared files: {sorted(unknown)}")
    for filename in _FILE_TITLES:
        (_DOCS_DIR / filename).write_text(_render(filename, by_file[filename]), encoding="utf-8")


if __name__ == "__main__":
    main()
