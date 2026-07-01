"""NER service stub for the ported pipeline.

sol-next's extract phase calls an external CAMeL Farasa NER service to validate
narrator names and find residual PERSON mentions. That service is disabled in
the ported config, so both entry points return their disabled-state values.
query_ner returns None (callers treat None as "no NER opinion" and keep names);
is_circuit_open returns False (no circuit to trip). Replace these with the real
client when NER is wired in.
"""

from __future__ import annotations

from typing import Any


def query_ner(_text: str) -> list[dict[str, Any]] | None:
    """Return None — the NER service is disabled in this port."""
    return None


def is_circuit_open() -> bool:
    """Return False — with no NER service there is no circuit breaker to trip."""
    return False
