import { useCallback, useState } from 'react';

import { isSearchMode, searchCorpus, searchFacets } from '../../lib/api/client';
import { wireCategories } from '../../lib/taxonomySelection';
import { SEARCH } from '../../lib/constants';
import type { SearchMode } from '../../lib/types';
import { CorpusResults } from './CorpusResults';
import type { CorpusFetcher } from './CorpusResults';
import './SearchResults.css';

function coerceMode(mode: string): SearchMode {
  return isSearchMode(mode) ? mode : SEARCH.DEFAULT_MODE;
}

/** Content-scope filters exactly as they round-trip through the URL (routes.ts
    RouteState's mode/categories/book): mode kept as a bare string for the same
    reason routes.ts keeps `scope` a string, so the hash layer never depends on
    api/client.ts. coerceMode above validates it back via isSearchMode. */
export interface ContentFilterRoute {
  mode: string;
  categories: string[];
  book: string;
}

/** The controlled-filters contract ContentScope accepts to lift its filters
    into the URL. Passed by the top-level content search (App.tsx, via
    useContentFilters below); omitted by embedded uses (the Qur'an
    verse-quotations panel), which keep page-local, resettable filters. */
export interface ContentFilters {
  mode: SearchMode;
  categories: ReadonlySet<string>;
  book: string;
  onMode: (mode: SearchMode) => void;
  onCategories: (categories: ReadonlySet<string>) => void;
  onBook: (book: string) => void;
}

/** Lifts the content scope's filters into App-owned state shaped for the URL:
    one hook call replaces three parallel useState triples in App.tsx, and
    keeps the coerce/reset/restore logic next to the ContentFilters contract
    it produces. `reset` clears the filters (a nav change); `restore` applies
    a parsed RouteState back (a popstate, i.e. Back/Forward). */
export function useContentFilters(initial: ContentFilterRoute): {
  filters: ContentFilters;
  route: ContentFilterRoute;
  reset: () => void;
  restore: (next: ContentFilterRoute) => void;
} {
  const [mode, setMode] = useState<SearchMode>(coerceMode(initial.mode));
  const [categories, setCategories] = useState<ReadonlySet<string>>(
    () => new Set(initial.categories),
  );
  const [book, setBook] = useState(initial.book);

  const reset = useCallback(() => {
    setMode(SEARCH.DEFAULT_MODE);
    setCategories(new Set());
    setBook('');
  }, []);
  const restore = useCallback((next: ContentFilterRoute) => {
    setMode(coerceMode(next.mode));
    setCategories(new Set(next.categories));
    setBook(next.book);
  }, []);

  return {
    filters: {
      mode,
      categories,
      book,
      onMode: setMode,
      onCategories: setCategories,
      onBook: setBook,
    },
    route: { mode, categories: wireCategories(categories), book },
    reset,
    restore,
  };
}

export interface ContentScopeProps {
  q: string;
  initialMode?: SearchMode;
  onOpenReader: (urn: string, page: number, query: string) => void;
  /** Controlled filters for the top-level content search (bookmarkable,
      survives the Reader round trip). Omitted for embedded uses, which fall
      back to local, page-scoped filters instead. */
  filters?: ContentFilters;
}

/** Full-text content search as a concordance page over ONE selection set:
    the distribution map's domain/category chips and the funnel popover are
    two views of the same set of category slugs (multi-select, OR'd
    server-side as repeated params), the toolbar shows the collapsed tokens
    and the union count, and the stream is the work-grouped anthology. Above
    the facet scan cap the map and picker are absent and SAY so. The Qurʾan
    scope reuses this with the resolved verse as `q` and broad mode. */
const corpusFetcher: CorpusFetcher = {
  matches: (q, scope) => searchCorpus(q, scope),
  facets: (q, mode, categories) => searchFacets(q, mode, categories),
};

/** Full-text content search over the corpus: a thin binding of the shared
    CorpusResults engine to the corpus endpoints, plus the URL-lifted filter
    contracts the top-level search wires through App.tsx. The Qur'an scope
    reuses this with the resolved verse as `q` and broad mode. */
export function ContentScope({
  q,
  initialMode = SEARCH.DEFAULT_MODE,
  onOpenReader,
  filters,
}: ContentScopeProps) {
  return (
    <CorpusResults
      q={q}
      onOpenReader={onOpenReader}
      fetcher={corpusFetcher}
      filters={filters}
      initialMode={initialMode}
    />
  );
}
