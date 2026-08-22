// almanac.ts — selectors over the served Hijri almanac (GET /api/almanac).
// The observance and chronicle tables live in the backend data contract
// (data/almanac.json); the client computes "today" (hijri.ts) and selects
// locally, so the payload carries no date and caches cleanly.

import type { Almanac, HistoryEvent, Observance } from './types';

// Rotor stride for the no-exact-match pick: co-prime with the table length so
// consecutive days walk the whole table instead of repeating a short cycle.
const ROTOR_STRIDE = 31;

/** Observances of one Hijri month, day-ordered. */
export function observancesForMonth(almanac: Almanac, month: number): Observance[] {
  return almanac.observances.filter((o) => o.month === month).sort((a, b) => a.day - b.day);
}

export interface TodayInHistory {
  event: HistoryEvent;
  onThisDay: boolean;
}

/** The event shown as "today in history": an exact Hijri-day match when one
    exists, otherwise a deterministic pick that rotates daily through the
    table (flagged so the UI says "from this era", not "on this day"). */
export function eventForDay(almanac: Almanac, month: number, day: number): TodayInHistory {
  const exact = almanac.events.find((e) => e.month === month && e.day === day);
  if (exact) return { event: exact, onThisDay: true };
  const index = (month * ROTOR_STRIDE + day) % almanac.events.length;
  const rotated = almanac.events[index];
  if (!rotated) throw new Error('almanac has no events to rotate through');
  return { event: rotated, onThisDay: false };
}
