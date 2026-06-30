"""Decision types and emit helpers for the hook dispatcher.

A handler returns a ``Decision``:
  * ``Decision.allow()``                              — no opinion, continue chain
  * ``Decision.advise(rule_id, msg, doc)``            — warn, continue chain
  * ``Decision.deny(rule_id, why, fix, doc)``         — block, end chain

The dispatcher emits the *first* deny it sees (chain-of-responsibility) and
exits with code 2 to tell Claude Code to abort the tool call. Advisories
print on stderr but do not change exit code.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Literal

Severity = Literal["allow", "advisory", "block"]


@dataclass(frozen=True, slots=True)
class Decision:
    """A handler verdict on a tool call."""

    severity: Severity
    rule_id: str = ""
    handler: str = ""
    why: str = ""
    fix: str = ""
    doc: str = ""
    metadata: dict[str, str] = field(default_factory=lambda: {})  # noqa: PIE807

    @staticmethod
    def allow(handler: str = "") -> Decision:
        """Return an allow verdict — no opinion, continue chain."""
        return Decision(severity="allow", handler=handler)

    @staticmethod
    def advise(
        *,
        handler: str,
        rule_id: str,
        why: str,
        fix: str = "",
        doc: str = "",
    ) -> Decision:
        """Return an advisory verdict — print warning, continue chain."""
        return Decision(
            severity="advisory",
            handler=handler,
            rule_id=rule_id,
            why=why,
            fix=fix,
            doc=doc,
        )

    @staticmethod
    def deny(
        *,
        handler: str,
        rule_id: str,
        why: str,
        fix: str,
        doc: str = "",
    ) -> Decision:
        """Return a deny verdict — first one wins, dispatcher will block."""
        return Decision(
            severity="block",
            handler=handler,
            rule_id=rule_id,
            why=why,
            fix=fix,
            doc=doc,
        )

    def is_block(self) -> bool:
        """True if this decision should halt the tool call."""
        return self.severity == "block"

    def is_advisory(self) -> bool:
        """True if this decision should warn but allow the tool call."""
        return self.severity == "advisory"


def emit_block(decision: Decision) -> None:
    """Print a structured block envelope to stderr and exit non-zero.

    Format combines a JSON line (for machine parsers / audit) followed by a
    human-readable block citing the rule + how to fix.
    """
    envelope = {"type": "harness.block", **asdict(decision)}
    print(json.dumps(envelope), file=sys.stderr)
    print("", file=sys.stderr)
    print(f"⛔ BLOCKED by {decision.handler} ({decision.rule_id})", file=sys.stderr)
    print(f"   why: {decision.why}", file=sys.stderr)
    print(f"   fix: {decision.fix}", file=sys.stderr)
    if decision.doc:
        print(f"   doc: {decision.doc}", file=sys.stderr)
    sys.exit(2)


def emit_advisory(decision: Decision) -> None:
    """Print an advisory envelope to stderr without exiting."""
    envelope = {"type": "harness.advisory", **asdict(decision)}
    print(json.dumps(envelope), file=sys.stderr)
    print(f"⚠️  {decision.handler} ({decision.rule_id}): {decision.why}", file=sys.stderr)
    if decision.fix:
        print(f"   fix: {decision.fix}", file=sys.stderr)
