import { describe, expect, test } from 'vitest';

import { HISTORY_EVENTS, OBSERVANCES, eventForDay, observancesForMonth } from './almanac';

describe('observance tables', () => {
  test('should keep every entry inside the Hijri calendar bounds', () => {
    for (const o of OBSERVANCES) {
      expect(o.month).toBeGreaterThanOrEqual(1);
      expect(o.month).toBeLessThanOrEqual(12);
      expect(o.day).toBeGreaterThanOrEqual(1);
      expect(o.day).toBeLessThanOrEqual(30);
    }
    for (const e of HISTORY_EVENTS) {
      expect(e.month).toBeGreaterThanOrEqual(1);
      expect(e.month).toBeLessThanOrEqual(12);
      expect(e.day).toBeGreaterThanOrEqual(1);
      expect(e.day).toBeLessThanOrEqual(30);
    }
  });
});

describe('observancesForMonth', () => {
  test('should return the month day-ordered', () => {
    const days = observancesForMonth(1).map((o) => o.day);
    expect(days.length).toBeGreaterThan(0);
    expect(days).toEqual([...days].sort((a, b) => a - b));
  });

  test('should return an empty list for a month with no entries', () => {
    expect(observancesForMonth(4).filter((o) => o.month !== 4)).toEqual([]);
  });
});

describe('eventForDay', () => {
  test('should return the exact event on an anniversary', () => {
    const { event, onThisDay } = eventForDay(1, 10);
    expect(onThisDay).toBe(true);
    expect(event.yearAh).toBe(61);
  });

  test('should fall back to a deterministic pick from the table', () => {
    const first = eventForDay(4, 2);
    const second = eventForDay(4, 2);
    expect(first.onThisDay).toBe(false);
    expect(first.event).toEqual(second.event);
    expect(HISTORY_EVENTS).toContain(first.event);
  });

  test('should walk different days to different fallback events', () => {
    const picks = new Set(
      [1, 2, 3, 4, 5].map((day) => eventForDay(4, day * 3).event.en),
    );
    expect(picks.size).toBeGreaterThan(1);
  });
});
