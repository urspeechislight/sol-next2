import { describe, expect, it } from 'vitest';

import type { CorpusMatch } from '../../lib/types';
import { groupByWork, refLabel } from './passages';

function hit(over: Partial<CorpusMatch>): CorpusMatch {
  return {
    urn: 'u_01',
    title_ar: 'كتاب',
    title_en: 'Book',
    author: 'Author',
    category: 'cat',
    volume: null,
    page: 1,
    snippet: 'نص',
    ...over,
  };
}

describe('groupByWork', () => {
  it('should group adjacent hits of one work and keep stream order', () => {
    const groups = groupByWork([
      hit({ title_ar: 'أ', page: 1 }),
      hit({ title_ar: 'أ', page: 2 }),
      hit({ title_ar: 'ب', page: 5 }),
    ]);
    expect(groups.map((g) => [g.title_ar, g.hits.length])).toEqual([
      ['أ', 2],
      ['ب', 1],
    ]);
  });

  it('should split homonym titles by author instead of merging them', () => {
    const groups = groupByWork([
      hit({ title_ar: 'التفسير', author: 'One' }),
      hit({ title_ar: 'التفسير', author: 'Two' }),
    ]);
    expect(groups).toHaveLength(2);
  });

  it('should merge a work split across a load-more boundary', () => {
    const first = [hit({ title_ar: 'أ', page: 1 })];
    const appended = [...first, hit({ title_ar: 'أ', page: 9 })];
    expect(groupByWork(appended)).toHaveLength(1);
  });
});

describe('refLabel', () => {
  it('should include the volume only when the work has one', () => {
    expect(refLabel(hit({ volume: 3, page: 214 }))).toBe('vol. 3 · p. 214');
    expect(refLabel(hit({ volume: null, page: 361 }))).toBe('p. 361');
  });
});
