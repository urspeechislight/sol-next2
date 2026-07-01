"""Block CSS-selector collisions across files under ``frontend/src``.

Why: the frontend ships one CSS file per primitive/component/feature under
``frontend/src`` (``Button.css``, ``Card.css``, ``reader.css``, ...) alongside
the token SSOT ``tokens.css``. Nothing at the language level stops the same
class body from being defined twice in two files, and once it is, the two
copies drift silently. This closes that hole for the static-file CSS layer.

What this handler does on every Write/Edit to a ``.css`` file under
``frontend/src``:

  1. Parse the new content. Collect every top-level selector that has
     a rule body (e.g. ``.ds-card { ... }``).
  2. Index every other ``.css`` file under ``frontend/src`` for the
     same shape.
  3. Block when an identical selector is already defined elsewhere.

Exempt:

  * ``:root`` and theme-scoped selectors like ``html[data-theme="dark"]``.
    Design tokens legitimately appear in both ``tokens.css`` and component
    sheets that introduce scoped token namespaces.
  * ``@media`` / ``@keyframes`` / ``@font-face`` and other at-rules.
    Component-specific breakpoints are expected.
  * Scrollbar/focus pseudo-elements the shared sheet may extend.

Mirrors the DRY-002 (``class_duplication``) shape for the CSS layer.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path

from ..context import HookContext
from ..decision import Decision
from ..paths import REPO_ROOT, is_in, relpath

HANDLER = "css_duplication"
RULE_ID = "UI-001"
DOC = "docs/quality-standards.md#ui-centralization"

_STATIC_DIR = "frontend/src"

_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
_RULE_RE = re.compile(r"([^{}@]+?)\s*\{[^{}]*\}", re.S)
_AT_RULE_HEAD_RE = re.compile(r"@[a-zA-Z-]+\b")

_EXEMPT_SELECTOR_RE = re.compile(
    r"^(?::root|html\[data-theme|@|::-webkit-scrollbar)",
    re.IGNORECASE,
)

logger = logging.getLogger(__name__)


def _strip_comments(text: str) -> str:
    """Remove /* ... */ comments so they don't masquerade as selectors."""
    return _COMMENT_RE.sub("", text)


def _skip_body_less_at_rule(text: str, at_end: int) -> int:
    """Return the index just past a body-less @-rule (e.g. ``@import url(...);``)."""
    semi = text.find(";", at_end)
    return semi + 1 if semi != -1 else len(text)


def _skip_at_rule_body(text: str, brace_open: int) -> int:
    """Return the index just past the matching ``}`` for the @-rule's body."""
    depth = 1
    k = brace_open + 1
    while k < len(text) and depth > 0:
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
        k += 1
    return k


def _strip_at_rule_blocks(text: str) -> str:
    """Remove @media/@supports/@keyframes blocks (with their bodies) entirely.

    Inner rules inside @media are page-specific responsive overrides, not
    top-level selector definitions — collisions across files are expected
    (every page that uses .metric-grid has its own breakpoint).
    Body-less @-rules (``@import``, ``@charset``) are also dropped.
    """
    out: list[str] = []
    i = 0
    while i < len(text):
        match = _AT_RULE_HEAD_RE.search(text, i)
        if match is None:
            out.append(text[i:])
            break
        out.append(text[i:match.start()])
        brace = text.find("{", match.end())
        if brace == -1:
            i = _skip_body_less_at_rule(text, match.end())
            continue
        i = _skip_at_rule_body(text, brace)
    return "".join(out)


def _normalize_selector(raw: str) -> str:
    """Collapse whitespace inside a selector list so equality is stable."""
    return re.sub(r"\s+", " ", raw.strip())


def _is_exempt(selector: str) -> bool:
    """True if `selector` is conventionally allowed to repeat across files."""
    return bool(_EXEMPT_SELECTOR_RE.match(selector))


def _selectors_in_text(text: str) -> set[str]:
    """Return the set of top-level rule selectors that own a body."""
    out: set[str] = set()
    stripped = _strip_at_rule_blocks(_strip_comments(text))
    for match in _RULE_RE.finditer(stripped):
        selector_list = _normalize_selector(match.group(1))
        if not selector_list or _is_exempt(selector_list):
            continue
        for selector in selector_list.split(","):
            sel = _normalize_selector(selector)
            if sel and not _is_exempt(sel):
                out.add(sel)
    return out


def _iter_static_css(exclude: Path | None) -> Iterable[Path]:
    """Yield CSS files under frontend/src/, skipping the file under edit."""
    for css in (REPO_ROOT / _STATIC_DIR).rglob("*.css"):
        if exclude is not None and css.resolve() == exclude:
            continue
        yield css


def _read_safely(css: Path) -> str | None:
    """Read the file, logging+skipping if it cannot be decoded."""
    try:
        return css.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        logger.warning("css_duplication: could not read %s; skipping", relpath(css), exc_info=True)
        return None


def _index_existing(exclude: Path | None) -> dict[str, Path]:
    """Return ``{selector: defining_file}`` for frontend/src/**/*.css."""
    index: dict[str, Path] = {}
    for css in _iter_static_css(exclude):
        text = _read_safely(css)
        if text is None:
            continue
        for selector in _selectors_in_text(text):
            index.setdefault(selector, css)
    return index


def check(ctx: HookContext) -> Decision:
    """Block when a CSS selector is already defined in another static/*.css."""
    if not ctx.is_write or ctx.new_content is None or ctx.suffix != "css":
        return Decision.allow(HANDLER)
    if not is_in(ctx.file_path, _STATIC_DIR):
        return Decision.allow(HANDLER)

    new_selectors = _selectors_in_text(ctx.new_content)
    if not new_selectors:
        return Decision.allow(HANDLER)

    index = _index_existing(ctx.file_path)
    for selector in sorted(new_selectors):
        if selector in index:
            other = relpath(index[selector])
            return Decision.deny(
                handler=HANDLER,
                rule_id=RULE_ID,
                why=(
                    f"Selector `{selector}` is already defined in `{other}`. "
                    "Two definitions of the same selector drift silently."
                ),
                fix=(
                    f"Move the rule into the canonical home (`{other}`) and "
                    "delete this copy. If the visual intent genuinely differs "
                    "per component, change the selector (e.g. add a scoped "
                    "parent like `.reader .ds-card`)."
                ),
                doc=DOC,
            )
    return Decision.allow(HANDLER)
