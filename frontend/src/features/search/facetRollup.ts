// facetRollup.ts: pure rollup of the query's per-category facet counts into
// the taxonomy's domains, the same domain -> category hierarchy the library
// rail walks. Facet slugs the taxonomy does not know are returned LOUDLY as
// `unmatched` (rendered as standalone chips), never silently dropped into a
// wrong domain sum.

import type { CategoryFacet, Domain } from '../../lib/types';

export interface DomainRollup {
  id: string;
  label: string;
  label_ar: string;
  /** Sum of the domain's matching categories' true counts. */
  count: number;
  /** The domain's categories that hold matches, heaviest first. */
  categories: CategoryFacet[];
}

export interface FacetRollup {
  /** Domains holding matches, heaviest first; empty domains are omitted. */
  domains: DomainRollup[];
  /** Facet slugs absent from the taxonomy, in facet order. */
  unmatched: CategoryFacet[];
}

export function rollupByDomain(domains: Domain[], facets: CategoryFacet[]): FacetRollup {
  const countOf = new Map(facets.map((f) => [f.slug, f.count]));
  const known = new Set<string>();
  const rolled: DomainRollup[] = [];
  for (const d of domains) {
    const cats: CategoryFacet[] = [];
    for (const c of d.categories) {
      known.add(c.slug);
      const count = countOf.get(c.slug);
      if (count !== undefined) cats.push({ slug: c.slug, count });
    }
    if (cats.length === 0) continue;
    cats.sort((a, b) => b.count - a.count || a.slug.localeCompare(b.slug));
    rolled.push({
      id: d.id,
      label: d.label,
      label_ar: d.label_ar,
      count: cats.reduce((n, c) => n + c.count, 0),
      categories: cats,
    });
  }
  rolled.sort((a, b) => b.count - a.count || a.id.localeCompare(b.id));
  return { domains: rolled, unmatched: facets.filter((f) => !known.has(f.slug)) };
}
