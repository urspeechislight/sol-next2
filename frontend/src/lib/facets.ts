// facets.ts: derive category facets from a result list on the client. The corpus
// scope gets facets from the server (/search/facets); every other scope
// (books by title/author, narrators) has no facet endpoint, so it groups its
// own returned rows here. One helper, so all client-faceted scopes count and
// filter categories identically. Pure.
import type { CategoryFacet } from './types';

/** Count items per category slug, descending by count then slug. Empty slugs are
    skipped (an uncategorised row contributes no facet). */
export function categoryFacets<T>(
  items: readonly T[],
  slugOf: (item: T) => string,
): CategoryFacet[] {
  const counts = new Map<string, number>();
  for (const item of items) {
    const slug = slugOf(item);
    if (!slug) continue;
    counts.set(slug, (counts.get(slug) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([slug, count]) => ({ slug, count }))
    .sort((a, b) => b.count - a.count || a.slug.localeCompare(b.slug));
}

/** Keep only items in ``category`` (or all items when no category is selected).
    The same client-side narrowing every faceted scope applies to its rows. */
export function byCategory<T>(
  items: readonly T[],
  category: string,
  slugOf: (item: T) => string,
): T[] {
  if (!category) return [...items];
  return items.filter((item) => slugOf(item) === category);
}
