import { useMemo } from 'react';

import { useDomains } from './useDomains';

/** Resolve a category slug to its English label via the domain taxonomy. The
    single place search and the library turn a category slug into a human label,
    so a raw slug is never shown to the reader. */
export function useCategoryLabels(): (slug: string) => string {
  const domains = useDomains();
  return useMemo(() => {
    const map = new Map<string, string>();
    for (const d of domains.data ?? []) for (const c of d.categories) map.set(c.slug, c.label);
    return (slug: string) => map.get(slug) ?? slug;
  }, [domains.data]);
}
