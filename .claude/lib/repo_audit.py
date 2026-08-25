"""Whole-repo SSOT/DRY audit gate (deterministic; fails commit + CI).

The PreToolUse harness checks one file at a time and cannot see cross-file
duplication, so the forks it structurally cannot catch are gated here instead:
this runs over the WHOLE repo (backend + frontend + scripts) at commit + CI.
Every check is deterministic and encodes facts about this repo's SSOT roles, so
a green run is a real ratchet and a violation is unambiguous. Clone detection
(jscpd) + dead-export detection (knip) layer on via the ``repo:audit`` script;
this module owns the rules no off-the-shelf tool knows about.

Module conventions for the constant tables below:

* ``_DS_SCAN_DIRS`` / ``_RAW_INTERACTIVE_RE`` / ``_RAW_INTERACTIVE_BASELINE`` —
  the design-system SSOT scan: feature/app code builds interactive controls from
  design-system primitives, never raw intrinsics; the ratchet baseline is the
  per-file count still tolerated, and it is empty (no raw element anywhere).
* ``_PRIMITIVES_GLOB`` / ``_CONTROL_PRIMITIVES`` / ``_TOKENS_CSS`` /
  ``_DARK_BLOCKS`` / ``_RAW_THEME_COLOR_RE`` — the deterministic gates for the
  forks a visual review surfaced (control shape, dark palette, search-scope
  framing): classes invisible to per-file harnesses and to jscpd because the
  scopes diverged in text rather than by copy-paste. ``_CONTROL_PRIMITIVES``
  lists the controls whose shape is SSOT via ``--radius-control`` (Spinner stays
  a pill and is deliberately absent); ``_RAW_THEME_COLOR_RE`` matches a raw
  colour literal (hex or oklch(), not the colour-space keyword).
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
_MAX_SAME_SUPPRESSION: Final[int] = 3
_SCAN_EXT: Final[tuple[str, ...]] = (".py", ".ts", ".tsx")
_SCAN_DIRS: Final[tuple[str, ...]] = ("src", "frontend/src", "scripts")

_CANONICAL: Final[dict[str, str]] = {
    "frontend/src/**/routes.ts": "frontend path/URL SSOT",
    "frontend/src/**/constants.ts": "frontend constants SSOT",
    "frontend/src/**/utils.ts": "frontend pure-helper SSOT",
    "frontend/src/**/types.ts": "frontend API-type SSOT",
    "frontend/src/**/arabic.ts": "frontend Arabic-fold SSOT",
    "src/backend/**/patterns.py": "backend regex/fold SSOT",
    "src/backend/core/paths.py": "repo-path SSOT",
}

_SINGLE_DEF: Final[tuple[tuple[str, str, str], ...]] = (
    ("fold_search", "src/backend/**/*.py", r"(?m)^def fold_search\b"),
    ("normalize_arabic", "src/backend/**/*.py", r"(?m)^def normalize_arabic\b"),
    ("data_path", "src/backend/**/*.py", r"(?m)^def data_path\b"),
    ("page_rows", "src/backend/**/*.py", r"(?m)^def page_rows\b"),
    ("book_table_rows", "src/backend/**/*.py", r"(?m)^def book_table_rows\b"),
    ("HadithGrade", "src/backend/**/*.py", r"(?m)^HadithGrade\s*[:=]"),
    ("REPO_ROOT", "src/backend/**/*.py", r"(?m)^REPO_ROOT\b"),
    ("foldSearch", "frontend/src/**/*.ts", r"export function foldSearch\b"),
    ("normalizeName", "frontend/src/**/*.ts", r"export function normalizeName\b"),
    ("clamp", "frontend/src/**/*.ts", r"export function clamp\b"),
    ("toArabicDigits", "frontend/src/**/*.ts", r"export function toArabicDigits\b"),
    ("pageCount", "frontend/src/**/*.ts", r"export function pageCount\b"),
    ("joinDots", "frontend/src/**/*.ts", r"export function joinDots\b"),
    ("NarratorCard", "frontend/src/**/*.tsx", r"export function NarratorCard\b"),
    ("buildHash", "frontend/src/**/*.ts", r"export function buildHash\b"),
    ("parseHash", "frontend/src/**/*.ts", r"export function parseHash\b"),
    ("useHashRoute", "frontend/src/**/*.ts", r"export function useHashRoute\b"),
)

_SUPPRESSION_RE: Final[re.Pattern[str]] = re.compile(
    r"#\s*pyright:\s*ignore\[(?P<py>[^\]]+)\]"
    r"|#\s*noqa:\s*(?P<noqa>[A-Z0-9]+)"
    r"|" + "eslint-" + r"disable(?:-next-line)?\s+(?P<eslint>[\w-]+)"
)
_SYSPATH_RE: Final[re.Pattern[str]] = re.compile(r"\bsys\.path\.(?:insert|append)\b")

_DS_SCAN_DIRS: Final[tuple[str, ...]] = (
    "frontend/src/features",
    "frontend/src/app",
    "frontend/src/components",
)
_RAW_INTERACTIVE_RE: Final[re.Pattern[str]] = re.compile(r"<(?:button|input|select|textarea)\b")
_RAW_INTERACTIVE_BASELINE: Final[dict[str, int]] = {}


@dataclass(frozen=True)
class Violation:
    """One SSOT/DRY breach: its rule, why it is one, the fix, and where."""

    rule_id: str
    why: str
    fix: str
    locations: tuple[str, ...]


def _scan_files(root: Path) -> list[Path]:
    """Every source file under the scanned dirs (py / ts / tsx)."""
    out: list[Path] = []
    for name in _SCAN_DIRS:
        base = root / name
        if base.exists():
            out += [p for p in base.rglob("*") if p.is_file() and p.suffix in _SCAN_EXT]
    return out


def check_canonical_modules(root: Path) -> list[Violation]:
    """Each SSOT-module glob must resolve to exactly one file."""
    out: list[Violation] = []
    for glob, role in _CANONICAL.items():
        hits = sorted(str(p.relative_to(root)) for p in root.glob(glob))
        if len(hits) != 1:
            out.append(
                Violation(
                    rule_id="AUDIT-SSOT-001",
                    why=f"{role}: expected exactly one file for '{glob}', found {len(hits)}.",
                    fix="Delete the duplicate(s); keep one canonical module and import it.",
                    locations=tuple(hits) or (glob,),
                )
            )
    return out


def check_single_definitions(root: Path) -> list[Violation]:
    """Each registered capability must be defined exactly once across the repo."""
    out: list[Violation] = []
    for label, glob, pattern in _SINGLE_DEF:
        rx = re.compile(pattern)
        hits: list[str] = []
        total = 0
        for path in root.glob(glob):
            if not path.is_file():
                continue
            found = len(rx.findall(path.read_text(encoding="utf-8")))
            if found:
                hits.append(str(path.relative_to(root)))
                total += found
        if total > 1:
            out.append(
                Violation(
                    rule_id="AUDIT-SSOT-002",
                    why=f"Capability '{label}' is defined {total} times; it must exist once.",
                    fix=f"Define '{label}' once; import it where needed; delete the copies.",
                    locations=tuple(sorted(hits)),
                )
            )
    return out


def check_suppression_budget(root: Path) -> list[Violation]:
    """No single suppression code may repeat beyond the budget (repetition of a
    targeted ignore is a structural problem, not many local exceptions)."""
    counts: Counter[str] = Counter()
    where: dict[str, set[str]] = {}
    for path in _scan_files(root):
        rel = str(path.relative_to(root))
        for match in _SUPPRESSION_RE.finditer(path.read_text(encoding="utf-8")):
            code = match.group("py") or match.group("noqa") or match.group("eslint") or "?"
            counts[code] += 1
            where.setdefault(code, set()).add(rel)
    out: list[Violation] = []
    for code, count in counts.items():
        if count > _MAX_SAME_SUPPRESSION:
            out.append(
                Violation(
                    rule_id="AUDIT-SUPPRESS-001",
                    why=f"Suppression '{code}' appears {count}x (budget {_MAX_SAME_SUPPRESSION}).",
                    fix=(
                        "Fix the root cause (config-scope the rule, change the pattern); "
                        "do not repeat the ignore."
                    ),
                    locations=tuple(sorted(where[code])),
                )
            )
    return out


def check_no_syspath(root: Path) -> list[Violation]:
    """App + script code must not manipulate sys.path (rely on the install)."""
    hits = sorted(
        str(p.relative_to(root))
        for d in ("src", "scripts")
        for p in (root / d).rglob("*.py")
        if (root / d).exists() and _SYSPATH_RE.search(p.read_text(encoding="utf-8"))
    )
    if not hits:
        return []
    return [
        Violation(
            rule_id="AUDIT-IMPORT-001",
            why=(
                "sys.path manipulation found; the backend package is importable "
                "via the editable install."
            ),
            fix="Remove sys.path.insert/append and import 'backend' directly.",
            locations=tuple(hits),
        )
    ]


def check_no_raw_interactive(root: Path) -> list[Violation]:
    """Feature/app/component code must build interactive controls from the
    design system, not raw <button>/<input>/<select>/<textarea>. A per-file count
    baseline ratchets the remaining debt down: a new raw element fails the gate,
    and a baseline that no longer matches its file is flagged so it only tightens."""
    out: list[Violation] = []
    seen: set[str] = set()
    for name in _DS_SCAN_DIRS:
        base = root / name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.tsx")):
            rel = str(path.relative_to(root))
            seen.add(rel)
            count = len(_RAW_INTERACTIVE_RE.findall(path.read_text(encoding="utf-8")))
            allowed = _RAW_INTERACTIVE_BASELINE.get(rel, 0)
            if count > allowed:
                out.append(
                    Violation(
                        rule_id="AUDIT-DS-001",
                        why=f"{rel}: {count} raw interactive element(s); only {allowed} allowed.",
                        fix=(
                            "Use a design-system primitive/component (Button, "
                            "IconButton, Pill, Input, Select); add one to the "
                            "design system if it is missing."
                        ),
                        locations=(rel,),
                    )
                )
            elif count < allowed:
                out.append(
                    Violation(
                        rule_id="AUDIT-DS-001",
                        why=(
                            f"{rel}: baseline of {allowed} is stale "
                            f"(file now has {count}); the ratchet only tightens."
                        ),
                        fix=(
                            f"Lower the _RAW_INTERACTIVE_BASELINE entry for "
                            f"'{rel}' to {count} (remove it at 0)."
                        ),
                        locations=(rel,),
                    )
                )
    for rel in sorted(set(_RAW_INTERACTIVE_BASELINE) - seen):
        out.append(
            Violation(
                rule_id="AUDIT-DS-001",
                why=f"{rel}: baseline entry references a file the scan did not find.",
                fix=f"Remove the stale _RAW_INTERACTIVE_BASELINE entry for '{rel}'.",
                locations=(rel,),
            )
        )
    return out


_PRIMITIVES_GLOB: Final[str] = "frontend/src/lib/design-system/primitives/*.css"
_CONTROL_PRIMITIVES: Final[frozenset[str]] = frozenset(
    {
        "Button.css",
        "IconButton.css",
        "Pill.css",
        "Segmented.css",
        "Chip.css",
        "Input.css",
        "Menu.css",
        "Pager.css",
    }
)
_TOKENS_CSS: Final[str] = "frontend/src/lib/design-system/tokens.css"
_DARK_BLOCKS: Final[tuple[str, ...]] = ("[data-theme='dark']", "[data-reader-theme='dark']")
_RAW_THEME_COLOR_RE: Final[re.Pattern[str]] = re.compile(r"#[0-9a-fA-F]{3,8}\b|oklch\(")
_SEARCH_GLOB: Final[str] = "frontend/src/features/search/*.tsx"
_SEARCH_FETCH_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:searchCorpus|searchBooks|searchQuran|getRijal)\b"
)


def check_control_radius(root: Path) -> list[Violation]:
    """Each interactive-control primitive takes its shape from --radius-control and
    never --radius-pill. The ratchet for the header/reader button shapes drifting
    apart (soft rectangles vs ovals)."""
    out: list[Violation] = []
    for path in sorted(root.glob(_PRIMITIVES_GLOB)):
        if path.name not in _CONTROL_PRIMITIVES:
            continue
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        if "var(--radius-pill)" in text:
            out.append(
                Violation(
                    rule_id="AUDIT-RADIUS-001",
                    why=f"{rel}: a control uses --radius-pill; control shape is one token.",
                    fix="Use border-radius: var(--radius-control); only Spinner stays a pill.",
                    locations=(rel,),
                )
            )
        if "var(--radius-control)" not in text:
            out.append(
                Violation(
                    rule_id="AUDIT-RADIUS-001",
                    why=f"{rel}: a control primitive does not reference --radius-control.",
                    fix="Set the control's border-radius to var(--radius-control).",
                    locations=(rel,),
                )
            )
    return out


def _css_block_body(text: str, selector: str) -> str:
    """Body of the first CSS rule whose selector is exactly ``selector``."""
    head = f"{selector} {{"
    start = text.find(head)
    if start < 0:
        return ""
    open_brace = start + len(head) - 1
    close = text.find("}", open_brace)
    return text[open_brace + 1 : close] if close > 0 else ""


def check_dark_palette(root: Path) -> list[Violation]:
    """The app dark theme and the reader dark theme both read from the one
    --palette-* source, so the reader cannot drift to a second (cooler) dark
    palette. A raw hex / oklch() literal inside either dark block is the tell."""
    path = root / _TOKENS_CSS
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    out: list[Violation] = []
    for selector in _DARK_BLOCKS:
        if _RAW_THEME_COLOR_RE.search(_css_block_body(text, selector)):
            out.append(
                Violation(
                    rule_id="AUDIT-THEME-001",
                    why=f"{selector}: raw colour literal; dark themes use --palette-* tokens.",
                    fix="Replace the hex/oklch() value with a var(--palette-...) token.",
                    locations=(_TOKENS_CSS,),
                )
            )
    return out


def check_scope_frame(root: Path) -> list[Violation]:
    """Every search scope that fetches results renders them through the shared
    ResultsFrame, never a hand-rolled count + record list. A scope may also
    delegate wholesale to the shared CorpusResults engine (a fetcher binding,
    as ContentScope and SemanticScope do) — a real JSX usage, not a comment
    mention, satisfies the rule. Closes the gap jscpd cannot see: scopes that
    diverged in text instead of sharing the frame."""
    out: list[Violation] = []
    for path in sorted(root.glob(_SEARCH_GLOB)):
        text = path.read_text(encoding="utf-8")
        if not _SEARCH_FETCH_RE.search(text):
            continue
        if "ResultsFrame" not in text and "<CorpusResults" not in text:
            rel = str(path.relative_to(root))
            out.append(
                Violation(
                    rule_id="AUDIT-SCOPE-001",
                    why=f"{rel}: a search scope renders results without the shared ResultsFrame.",
                    fix="Render results through ResultsFrame (features/search/ResultsFrame.tsx).",
                    locations=(rel,),
                )
            )
    return out


def audit(root: Path) -> list[Violation]:
    """Run every whole-repo check against ``root`` and collect violations."""
    return [
        *check_canonical_modules(root),
        *check_single_definitions(root),
        *check_suppression_budget(root),
        *check_no_syspath(root),
        *check_no_raw_interactive(root),
        *check_control_radius(root),
        *check_dark_palette(root),
        *check_scope_frame(root),
    ]


def main() -> int:
    """Audit the repo (argv[1] or this checkout); print + exit non-zero on any breach."""
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _REPO_ROOT
    violations = audit(root)
    if not violations:
        print("repo:audit — no SSOT/DRY violations.")
        return 0
    for v in violations:
        print(f"\n[BLOCK] {v.rule_id}\n   why: {v.why}\n   fix: {v.fix}")
        for loc in v.locations:
            print(f"   - {loc}")
    print(f"\nrepo:audit FAILED: {len(violations)} violation(s).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
