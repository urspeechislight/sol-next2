import { describe, expect, test } from 'vitest';

import { byCategory, categoryFacets } from './facets';

interface Row {
  id: number;
  category: string;
}
const slug = (r: Row) => r.category;
const rows: Row[] = [
  { id: 1, category: 'fiqh' },
  { id: 2, category: 'hadith' },
  { id: 3, category: 'fiqh' },
  { id: 4, category: '' },
  { id: 5, category: 'fiqh' },
  { id: 6, category: 'hadith' },
];

describe('categoryFacets', () => {
  test('should count items per category slug', () => {
    expect(categoryFacets(rows, slug)).toEqual([
      { slug: 'fiqh', count: 3 },
      { slug: 'hadith', count: 2 },
    ]);
  });

  test('should sort by count descending then slug ascending', () => {
    const tied: Row[] = [
      { id: 1, category: 'zoology' },
      { id: 2, category: 'adab' },
    ];
    expect(categoryFacets(tied, slug).map((f) => f.slug)).toEqual(['adab', 'zoology']);
  });

  test('should skip empty slugs and return nothing for an empty list', () => {
    expect(categoryFacets([{ id: 1, category: '' }], slug)).toEqual([]);
    expect(categoryFacets([], slug)).toEqual([]);
  });
});

describe('byCategory', () => {
  test('should return all rows as a copy when no category is selected', () => {
    const out = byCategory(rows, '', slug);
    expect(out).toHaveLength(rows.length);
    expect(out).not.toBe(rows);
  });

  test('should keep only rows in the selected category', () => {
    expect(byCategory(rows, 'hadith', slug).map((r) => r.id)).toEqual([2, 6]);
  });
});
