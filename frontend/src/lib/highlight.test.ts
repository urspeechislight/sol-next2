import { describe, expect, test } from 'vitest';

import { highlightSegments } from './highlight';

function matched(text: string, query: string): string {
  return highlightSegments(text, query)
    .filter((s) => s.match)
    .map((s) => s.text)
    .join('');
}

describe('highlightSegments (search-fold aware)', () => {
  test('should mark a diacritic-insensitive match keeping original text', () => {
    const segs = highlightSegments('قَالَ رَسُولُ اللَّه', 'رسول');
    expect(segs.some((s) => s.match && s.text.includes('رَسُول'))).toBe(true);
  });

  test('should mark an alef-hamza variant, folding letters like the index', () => {
    expect(matched('لهم أولياء عظيم', 'اولياء')).toContain('أولياء');
  });

  test('should leave the whole string unmatched when the query is absent', () => {
    expect(highlightSegments('قال رسول', 'xyz')).toEqual([{ text: 'قال رسول', match: false }]);
  });

  test('should match across a stripped space-surrounded waqf sign', () => {
    // The verse query carries Quranic waqf signs (ۚ) between words; the page
    // quotes the same verse without them. Folding the signs away leaves a double
    // space in the query that must not break the contiguous phrase match.
    const query = 'وَعَدْلًا ۚ لَا مُبَدِّلَ لِكَلِمَاتِهِ';
    const page = 'صدقا وعدلا لا مبدل لكلماته وهو السميع';
    expect(matched(page, query)).toContain('وعدلا لا مبدل لكلماته');
  });
});
