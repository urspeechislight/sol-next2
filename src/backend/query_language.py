"""The boolean search query language: the one grammar definition, parser, and
error type for full-text queries.

This mirrors the canonical module in the consolidated search backend
(sol-next3 ``backend/query_language.py``); both run the identical golden test
table, so the two implementations cannot drift without a test failing. The
reader's local paths (in-book scan, Quran search) parse with this module; the
proxied corpus path forwards the raw query to the backend, which parses the
same grammar server-side.

GRAMMAR:

    query   := include { "+" include } [ "NOT" exclude { "+" exclude } ]
    include := WORD { " " WORD }
    exclude := WORD { " " WORD }

  * A standalone "+" token joins clauses that must ALL match (AND).
  * A standalone uppercase "NOT" token switches every clause after it to
    exclusion. Lowercase "not" is ordinary text: an English phrase like
    "do not disturb" must never be parsed as an operator.
  * Operators are only operators as standalone tokens: "c++" and "a+b" are
    content words.
  * Each clause is a phrase matched exactly as today: the shared fold rule
    (diacritics dropped, alef/yaa/taa variants folded) applies to clause and
    text alike, so matching is diacritic-insensitive in both languages.

ERRORS are loud, never reinterpreted: a query whose operators leave it with
no include clause ("NOT x", "+ +") raises QueryLanguageError, mapped to 422
by main.py. "Everything except X" is not expressible — that would be an
unbounded scan, and the service does not guess.
"""

from __future__ import annotations

from dataclasses import dataclass

_AND_OPERATOR = "+"
_NOT_OPERATOR = "NOT"


class QueryLanguageError(ValueError):
    """The query used boolean syntax but formed no valid include clause."""


@dataclass(frozen=True, slots=True)
class BooleanQuery:
    """A parsed boolean query: phrase clauses to require and to exclude."""

    includes: tuple[str, ...]
    excludes: tuple[str, ...]


def parse_query(query: str) -> BooleanQuery | None:
    """Parse ``query`` per the module grammar; None when it carries no operators.

    ``None`` is the plain-mode signal: the caller's default behavior applies
    unchanged, so callers never branch on operator detection themselves.
    """
    tokens = query.split()
    if _AND_OPERATOR not in tokens and _NOT_OPERATOR not in tokens:
        return None

    includes: list[str] = []
    excludes: list[str] = []
    clause: list[str] = []
    current = includes

    def flush() -> None:
        """Close the current clause into the active list, dropping empties."""
        if clause:
            current.append(" ".join(clause).strip('"'))
            clause.clear()

    for tok in tokens:
        if tok == _AND_OPERATOR:
            flush()
        elif tok == _NOT_OPERATOR:
            flush()
            current = excludes
        else:
            clause.append(tok)
    flush()

    includes = [c for c in includes if c]
    excludes = [c for c in excludes if c]
    if not includes:
        raise QueryLanguageError(
            "boolean query has no include clause: nothing to require "
            "(a query may not start with NOT, and operators alone are not a query)"
        )
    return BooleanQuery(includes=tuple(includes), excludes=tuple(excludes))
