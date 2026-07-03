// worksFilter.ts: the one definition of the library's combinable work facets
// (era / author / foundational) and sort orders. FilterBar renders these
// controls; FacetedWorksList applies them; nothing else re-implements either.

import type { Work } from '../../lib/types';
import { byDeathThenTitle, centuryOf, groupByEra, matchesAuthor } from './lib';

export type SortMode = 'canonical' | 'era' | 'title' | 'author' | 'volumes';

export interface Filters {
  era: number | null;
  author: string;
  foundational: boolean;
  sort: SortMode;
}

export const DEFAULT_FILTERS: Filters = { era: null, author: '', foundational: false, sort: 'era' };

/** The work's editorial-rank tier as SERVED (Work.canonical_tier): the tier
    table has one owner, the backend's Canonical vocabulary, so client-side
    re-ordering of an assembled scope and server-side ``sort=canonical``
    paging can no longer disagree. Unranked works sort after every tier. */
function canonicalTier(work: Work): number {
  return work.canonical_tier ?? Number.MAX_SAFE_INTEGER;
}

/** Order a scope for one sort mode. ``era`` yields the century-section order;
    ``canonical`` leads with the most authoritative tier (then death year), the
    honest "most famous first" a search surface defaults to. */
function orderWorks(works: Work[], sort: SortMode): Work[] {
  if (sort === 'era') return groupByEra(works).flatMap((g) => g.works);
  const copy = [...works];
  if (sort === 'canonical')
    return copy.sort((a, b) => canonicalTier(a) - canonicalTier(b) || byDeathThenTitle(a, b));
  if (sort === 'title') return copy.sort((a, b) => a.title_ar.localeCompare(b.title_ar, 'ar'));
  if (sort === 'author')
    return copy.sort(
      (a, b) =>
        (a.author ?? a.author_ar ?? '').localeCompare(b.author ?? b.author_ar ?? '') ||
        a.title_ar.localeCompare(b.title_ar, 'ar'),
    );
  return copy.sort(
    (a, b) => b.volume_count - a.volume_count || (b.page_count ?? 0) - (a.page_count ?? 0),
  );
}

/** Apply the combinable facets, then the sort. */
export function applyFilters(works: Work[], f: Filters): Work[] {
  let out = works;
  if (f.era !== null) out = out.filter((w) => centuryOf(w) === f.era);
  if (f.author.trim()) out = out.filter((w) => matchesAuthor(w, f.author));
  if (f.foundational) out = out.filter((w) => w.canonical === 'primary_reference');
  return orderWorks(out, f.sort);
}
