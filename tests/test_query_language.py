"""Golden-vector tests for the boolean query language (src/backend/query_language.py).

The table mirrors the canonical vectors in sol-next3's
tests/backend/test_search.py: both implementations run the identical cases, so
the reader's local parser and the search backend's parser cannot drift without
a test failing in one repo or the other.
"""

from __future__ import annotations

import pytest

from backend.query_language import QueryLanguageError, parse_query

_PARSE_GOLDEN = [
    ("a b", None),  # no operators -> plain match mode
    ("do not disturb", None),  # lowercase "not" is content, never an operator
    ("a+b", None),  # operators are operators only as standalone tokens
    ("a b + c d", (("a b", "c d"), ())),
    ('"a b" + "c d"', (("a b", "c d"), ())),  # quotes are decorative
    ("a b NOT c d", (("a b",), ("c d",))),
    ("a + b NOT c NOT d", (("a", "b"), ("c", "d"))),
    ("الله + الرحمن NOT الشيطان", (("الله", "الرحمن"), ("الشيطان",))),
]


def test_should_parse_boolean_grammar_golden_vectors() -> None:
    """Every golden vector parses to its documented AST (or None for plain mode)."""
    for query, expected in _PARSE_GOLDEN:
        parsed = parse_query(query)
        if expected is None:
            assert parsed is None, query
        else:
            assert parsed is not None, query
            assert (parsed.includes, parsed.excludes) == expected, query


def test_should_reject_boolean_query_without_include() -> None:
    """Operator grammars that leave nothing to require raise QueryLanguageError."""
    for bad in ("NOT x", "+ +", "NOT"):
        with pytest.raises(QueryLanguageError):
            parse_query(bad)
