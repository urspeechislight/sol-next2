"""Pydantic DTOs for the Hijri almanac: month observances + chronicle events.

The almanac is reference data (like the surah name table), served whole from
``data/almanac.json``. The client owns "today": the Hijri date is computed
browser-side, so no request carries a date and the payload caches cleanly.
Dates follow the common Twelver reckoning; observed dates vary by
moon-sighting and community.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from backend.core.constants import CALENDAR__HIJRI_MONTH_DAY_MAX, CALENDAR__HIJRI_MONTHS
from backend.models._base import FrozenModel

ObservanceKind = Literal["eid", "mourning", "birth", "night", "observance"]


class HijriDate(FrozenModel):
    """A month + day reference in the Hijri year, the key both entry kinds share."""

    month: int = Field(ge=1, le=CALENDAR__HIJRI_MONTHS)
    day: int = Field(ge=1, le=CALENDAR__HIJRI_MONTH_DAY_MAX)


class Observance(HijriDate):
    """One recurring date in the Hijri year."""

    en: str
    ar: str
    kind: ObservanceKind


class HistoryEvent(HijriDate):
    """One chronicle entry keyed to a Hijri month + day."""

    year_ah: int = Field(ge=0, description="0 marks an event before the hijra.")
    en: str
    detail: str


class Almanac(FrozenModel):
    """The served almanac: every observance + every chronicle entry."""

    observances: list[Observance] = Field(min_length=1)
    events: list[HistoryEvent] = Field(min_length=1)
