import { describe, expect, it } from 'vitest';

import type { Domain } from '../../lib/types';
import { rollupByDomain } from './facetRollup';

function domain(id: string, slugs: string[]): Domain {
  return {
    id,
    label: id,
    label_ar: id,
    blurb: '',
    categories: slugs.map((slug) => ({
      slug,
      label: slug,
      label_ar: slug,
      count: 0,
      volume_count: 0,
      tradition: 'shared' as const,
    })),
  };
}

const TAXONOMY = [domain('fiqh', ['hanafi', 'maliki']), domain('hadith', ['sunni-hadith'])];

describe('rollupByDomain', () => {
  it('should sum category counts into their domain, heaviest first', () => {
    const rollup = rollupByDomain(TAXONOMY, [
      { slug: 'hanafi', count: 10 },
      { slug: 'maliki', count: 5 },
      { slug: 'sunni-hadith', count: 40 },
    ]);
    expect(rollup.domains.map((d) => [d.id, d.count])).toEqual([
      ['hadith', 40],
      ['fiqh', 15],
    ]);
    expect(rollup.domains[1].categories[0].slug).toBe('hanafi');
  });

  it('should omit domains with no matching categories', () => {
    const rollup = rollupByDomain(TAXONOMY, [{ slug: 'hanafi', count: 1 }]);
    expect(rollup.domains.map((d) => d.id)).toEqual(['fiqh']);
  });

  it('should surface facet slugs the taxonomy does not know as unmatched', () => {
    const rollup = rollupByDomain(TAXONOMY, [
      { slug: 'hanafi', count: 1 },
      { slug: 'lost-slug', count: 7 },
    ]);
    expect(rollup.unmatched).toEqual([{ slug: 'lost-slug', count: 7 }]);
    expect(rollup.domains.map((d) => d.count)).toEqual([1]);
  });
});
