"""Agent guardrail harness — control-plane library.

This package powers `.claude/hooks/` dispatcher scripts. Hook scripts read
tool input from stdin, invoke a chain of handler callables (each returns a
:class:`Decision`), and emit a structured block to stderr with non-zero exit
code if any handler denied. See ``.claude/lib/dispatcher.py`` for the core
chain-of-responsibility.

Design tenets:
  * Pure Python, no LLM calls, no network — handlers must be deterministic.
  * First deny wins. Advisory decisions accumulate but do not block.
  * Crashes are treated as denies (fail-closed).
  * Every decision is appended to ``.claude/audit/events.jsonl``.
"""

__version__ = "0.1.0"
