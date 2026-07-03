// taxonomy.ts:the one set of derivations over the served Domain[] taxonomy.
// Every surface that states the library's extent (the landing masthead, the
// fihrist band, the Browse rail) sums through these, so the same corpus can
// never announce two different sizes on one screen.

import type { Domain } from './types';

/** Total work count across a category list. */
export function sumCount(cats: { count: number }[]): number {
  return cats.reduce((n, c) => n + c.count, 0);
}

/** One domain's extent: works + volumes summed across its categories. */
export function domainTotals(domain: Domain): { works: number; volumes: number } {
  let works = 0;
  let volumes = 0;
  for (const c of domain.categories) {
    works += c.count;
    volumes += c.volume_count;
  }
  return { works, volumes };
}

/** The whole library's extent, summed live from the taxonomy. */
export function corpusTotals(domains: Domain[]): {
  works: number;
  volumes: number;
  categories: number;
  domains: number;
} {
  let works = 0;
  let volumes = 0;
  let categories = 0;
  for (const d of domains) {
    const t = domainTotals(d);
    works += t.works;
    volumes += t.volumes;
    categories += d.categories.length;
  }
  return { works, volumes, categories, domains: domains.length };
}
