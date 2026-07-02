import { describe, expect, test } from 'vitest';

import { eventForDay, observancesForMonth } from './almanac';
import type { Almanac } from './types';

const ALMANAC: Almanac = {
  observances: [
    { month: 1, day: 10, en: 'ʿĀshūrāʾ', ar: 'عاشوراء', kind: 'mourning' },
    { month: 1, day: 1, en: 'Hijri New Year', ar: 'رأس السنة الهجرية', kind: 'observance' },
    { month: 12, day: 18, en: 'ʿĪd al-Ghadīr', ar: 'عيد الغدير', kind: 'eid' },
  ],
  events: [
    { month: 1, day: 10, year_ah: 61, en: 'The Battle of Karbalāʾ', detail: 'Karbalāʾ.' },
    { month: 9, day: 17, year_ah: 2, en: 'The Battle of Badr', detail: 'Badr.' },
    { month: 12, day: 18, year_ah: 10, en: 'The pond of Ghadīr Khumm', detail: 'Ghadīr.' },
  ],
};

describe('observancesForMonth', () => {
  test('should return only the month, day-ordered', () => {
    const days = observancesForMonth(ALMANAC, 1).map((o) => o.day);
    expect(days).toEqual([1, 10]);
  });

  test('should return an empty list for a month with no entries', () => {
    expect(observancesForMonth(ALMANAC, 4)).toEqual([]);
  });
});

describe('eventForDay', () => {
  test('should return the exact event on an anniversary', () => {
    const { event, onThisDay } = eventForDay(ALMANAC, 1, 10);
    expect(onThisDay).toBe(true);
    expect(event.year_ah).toBe(61);
  });

  test('should fall back to a deterministic pick from the table', () => {
    const first = eventForDay(ALMANAC, 4, 2);
    const second = eventForDay(ALMANAC, 4, 2);
    expect(first.onThisDay).toBe(false);
    expect(first.event).toEqual(second.event);
    expect(ALMANAC.events).toContain(first.event);
  });

  test('should walk different days to different fallback events', () => {
    const picks = new Set([1, 2, 3, 4, 5].map((day) => eventForDay(ALMANAC, 4, day).event.en));
    expect(picks.size).toBeGreaterThan(1);
  });
});
