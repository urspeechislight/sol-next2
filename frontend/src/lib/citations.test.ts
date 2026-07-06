import { describe, expect, it } from 'vitest';

import { citationSegments } from './citations';
import type { QuranCitation } from './types';

const cite = (offset: number, length: number, surah: number, aya: number): QuranCitation => ({
  offset,
  length,
  surah,
  aya_start: aya,
  aya_end: aya,
  verse_match: 'exact',
});

describe('citationSegments', () => {
  it('should return one text segment when there are no citations', () => {
    expect(citationSegments('نص عربي', [])).toEqual([{ type: 'text', value: 'نص عربي' }]);
  });

  it('should wrap a citation and keep the surrounding text', () => {
    const text = 'قال [البقرة] ثم';
    const segs = citationSegments(text, [cite(4, 8, 2, 255)]);
    expect(segs).toEqual([
      { type: 'text', value: 'قال ' },
      { type: 'cite', value: '[البقرة]', surah: 2, ayaStart: 255, ayaEnd: 255 },
      { type: 'text', value: ' ثم' },
    ]);
  });

  it('should reproduce the input exactly when segments are concatenated', () => {
    const text = 'a[x]b[y]c';
    const segs = citationSegments(text, [cite(1, 3, 2, 1), cite(5, 3, 3, 4)]);
    expect(segs.map((s) => s.value).join('')).toBe(text);
  });

  it('should skip an overlapping or out-of-bounds citation', () => {
    const text = 'short';
    expect(citationSegments(text, [cite(3, 99, 1, 1)])).toEqual([{ type: 'text', value: 'short' }]);
  });
});
