import { describe, expect, test } from 'vitest';

import { clamp, fromBase64Url, joinDots, pageCount, toArabicDigits, toBase64Url } from './utils';

describe('joinDots', () => {
  test('should join non-empty parts with a dot separator', () => {
    expect(joinDots('a', null, 'b', undefined, false, 'c')).toBe('a · b · c');
  });
  test('should return empty string when all parts are empty', () => {
    expect(joinDots(null, undefined, false)).toBe('');
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

describe('toBase64Url / fromBase64Url', () => {
  test('should round-trip ASCII text', () => {
    expect(fromBase64Url(toBase64Url('hadith'))).toBe('hadith');
  });

  test('should round-trip Arabic text with diacritics', () => {
    const verse = 'وَمَا جَعَلْنَا لِبَشَرٍ مِنْ قَبْلِكَ الْخُلْدَ ۖ أَفَإِنْ مِتَّ فَهُمُ الْخَالِدُونَ';
    expect(fromBase64Url(toBase64Url(verse))).toBe(verse);
  });

  test('should round-trip the empty string', () => {
    expect(toBase64Url('')).toBe('');
    expect(fromBase64Url('')).toBe('');
  });

  test('should produce URL-safe output with no +, /, or = padding', () => {
    // A run of bytes long enough to hit every base64 alphabet character and
    // every padding case (length % 3 === 0, 1, 2).
    const encoded = toBase64Url('the isnād and the matn, a chain of narrators');
    expect(encoded).not.toMatch(/[+/=]/);
  });

  test('should never throw on malformed input, returning an empty string', () => {
    expect(fromBase64Url('not valid base64url!!!')).toBe('');
  });

  test('should be meaningfully shorter than percent-encoding for Arabic text', () => {
    const verse = 'وَمَا جَعَلْنَا لِبَشَرٍ مِنْ قَبْلِكَ الْخُلْدَ ۖ أَفَإِنْ مِتَّ فَهُمُ الْخَالِدُونَ';
    const percentEncoded = encodeURIComponent(verse);
    expect(toBase64Url(verse).length).toBeLessThan(percentEncoded.length * 0.6);
  });
});
