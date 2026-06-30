import { describe, expect, test } from 'vitest';

import { clamp, formatDeath, joinDots, pageCount, toArabicDigits } from './utils';

describe('joinDots', () => {
  test('should join non-empty parts with a dot separator', () => {
    expect(joinDots('a', null, 'b', undefined, false, 'c')).toBe('a · b · c');
  });
  test('should return empty string when all parts are empty', () => {
    expect(joinDots(null, undefined, false)).toBe('');
  });
});

describe('formatDeath', () => {
  test('should format both hijri and gregorian years', () => {
    expect(formatDeath(150, 767)).toBe('ت 150هـ · 767م');
  });
  test('should omit a missing part', () => {
    expect(formatDeath(null, 767)).toBe('767م');
    expect(formatDeath(150, null)).toBe('ت 150هـ');
    expect(formatDeath(null, null)).toBe('');
  });
});

describe('pageCount', () => {
  test('should return at least one page even for zero items', () => {
    expect(pageCount(0, 10)).toBe(1);
  });
  test('should round up partial pages', () => {
    expect(pageCount(25, 10)).toBe(3);
  });
});

describe('clamp', () => {
  test('should bound a value into the inclusive range', () => {
    expect(clamp(5, 1, 10)).toBe(5);
    expect(clamp(15, 1, 10)).toBe(10);
    expect(clamp(-3, 1, 10)).toBe(1);
  });
});

describe('toArabicDigits', () => {
  test('should map Western digits to Arabic-Indic digits', () => {
    expect(toArabicDigits(1234567890)).toBe('١٢٣٤٥٦٧٨٩٠');
  });
});
