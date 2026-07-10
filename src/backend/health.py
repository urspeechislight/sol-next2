"""Aggregate health probe: exercise each major subsystem for a client heartbeat.

The liveness route ``/health`` in ``main.py`` only reports that the process is up.
The ``/api/health`` route (registered in ``main.py`` so it stays reachable through
the Vite ``/api`` proxy the frontend uses) calls ``health`` below to exercise the
read path of every major endpoint, so a 5-second heartbeat can surface a broken
data source, or an unreachable backend, before a user meets a bare 500.

A probe must report ANY failure rather than crash the endpoint, so the probes run
through ``asyncio.gather(return_exceptions=True)``: a raised exception becomes a
captured result the report records, not a propagated error and not a swallowed one.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Final

from backend.models.health import HealthCheck, HealthReport
from backend.repositories import almanac as almanac_repo
from backend.repositories import books as books_repo
from backend.repositories import citations as citations_repo
from backend.repositories import daily as daily_repo
from backend.repositories import domains as domains_repo
from backend.repositories import quran as quran_repo
from backend.repositories import registry

_ERROR_DETAIL_MAX: Final[int] = 200

_PROBES: Final[tuple[tuple[str, Callable[[], object]], ...]] = (
    ("domains", domains_repo.list_domains),
    ("books", lambda: books_repo.list_books(limit=1)),
    ("rijal", lambda: registry.list_rijal(registry.RijalFilter(), limit=1)),
    ("person", lambda: registry.list_person(registry.PersonFilter(), limit=1)),
    ("quran", lambda: quran_repo.get_surah(1)),
    ("daily", daily_repo.get_today),
    ("almanac", almanac_repo.get_almanac),
    ("citations", lambda: citations_repo.books_citing(1, 1)),
)


async def _call_probe(probe: Callable[[], object]) -> object:
    """Invoke one probe; a raised exception is captured by the gathering caller."""
    return probe()


async def health() -> HealthReport:
    """Probe every subsystem and report per-subsystem status; returns 200 either way."""
    outcomes = await asyncio.gather(
        *(_call_probe(probe) for _, probe in _PROBES), return_exceptions=True
    )
    checks = [
        HealthCheck(
            name=name,
            ok=not isinstance(outcome, BaseException),
            error=""
            if not isinstance(outcome, BaseException)
            else f"{type(outcome).__name__}: {outcome}"[:_ERROR_DETAIL_MAX],
        )
        for (name, _), outcome in zip(_PROBES, outcomes, strict=True)
    ]
    status = "ok" if all(check.ok for check in checks) else "degraded"
    return HealthReport(status=status, checks=checks)
