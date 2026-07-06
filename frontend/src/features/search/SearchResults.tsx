import { useEffect, useState } from 'react';

import { Heading, Text } from '../../lib/design-system';
import { getRijal } from '../../lib/api/client';
import type { SearchScope } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import { byCategory, categoryFacets } from '../../lib/facets';
import type { Page, RijalEntry } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { useCategoryLabels } from '../../lib/useCategoryLabels';
import { WorksQueryResults } from '../library/WorksQueryResults';
import { NarratorCard } from '../narrators/NarratorCard';
import { ContentScope } from './ContentScope';
import type { ContentFilters } from './ContentScope';
import { QuranScope } from './QuranScope';
import { ResultsFrame } from './ResultsFrame';
import '../screens.css';
import './SearchResults.css';

/** The narrator scope has no server facet endpoint: fetch one page, derive the
    category filter from the returned rows (categoryFacets), apply it on the
    client, and render through the shared ResultsFrame. */
function NarratorScope({ q }: { q: string }) {
  const res = useAsync<Page<RijalEntry>>(() => getRijal({ q, limit: PAGE.facetLimit }), [q]);
  const labelOf = useCategoryLabels();
  const [category, setCategory] = useState('');
  useEffect(() => setCategory(''), [q]);

  const items = res.data?.items ?? [];
  const shown = byCategory(items, category, (e) => e.category);
  const total = category ? shown.length : (res.data?.total ?? 0);
  const empty =
    res.data && shown.length === 0
      ? category
        ? 'No narrators in this category.'
        : `No narrators match “${q}”.`
      : null;

  return (
    <ResultsFrame
      filters={{
        categories: categoryFacets(items, (e) => e.category),
        labelOf,
        category,
        total,
        onCategory: setCategory,
        onClear: () => setCategory(''),
      }}
      loading={res.loading}
      loadingLabel="Searching narrators"
      error={res.error ? `Narrator search is unavailable: ${res.error.message}` : null}
      empty={empty}
    >
      {res.data ? (
        <div className="ds-records">
          {shown.map((e) => (
            <NarratorCard key={e.id} item={e} />
          ))}
        </div>
      ) : null}
    </ResultsFrame>
  );
}

export interface SearchResultsProps {
  query: string;
  scope: SearchScope;
  /** Drill a Qurʾān verse hit into the reader at that exact āya (App.tsx's
      openVerse) — the same navigation a citation link in the reader uses. */
  onOpenVerse: (surah: number, ayah: number) => void;
  onOpenReader: (urn: string, page: number, query: string) => void;
  /** The top-level content search's URL-lifted filters (App.tsx, via
      useContentFilters). Passed straight to the content scope so a search's
      exact filters survive a bookmark, a reload, or a Reader visit and back. */
  contentFilters: ContentFilters;
}

/** The search overlay: one query, four scopes. Works is the catalog primitive
    (volume-folded, canonical-ranked, the library's own faceted grammar);
    content / quran are the passage primitives; narrator searches the rijal
    registry. Every scope pages honestly; none caps silently. */
export function SearchResults({
  query,
  scope,
  onOpenVerse,
  onOpenReader,
  contentFilters,
}: SearchResultsProps) {
  const q = query.trim();
  return (
    <section>
      <header className="scr__head">
        <Text size="xs" tone="accent" weight="semibold" className="scr__eyebrow">
          Search · بحث
        </Text>
        <Heading level={1}>Results for “{q}”</Heading>
      </header>
      {scope === 'content' ? (
        <ContentScope q={q} onOpenReader={onOpenReader} filters={contentFilters} />
      ) : null}
      {scope === 'quran' ? (
        <QuranScope q={q} onOpenVerse={onOpenVerse} onOpenReader={onOpenReader} />
      ) : null}
      {scope === 'works' ? (
        <WorksQueryResults q={q} onOpen={(urn, page) => onOpenReader(urn, page ?? 1, '')} />
      ) : null}
      {scope === 'narrator' ? <NarratorScope q={q} /> : null}
    </section>
  );
}
