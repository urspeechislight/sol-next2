import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { Text } from '../../lib/design-system';
import { LoadMoreFoot } from '../../lib/LoadMoreFoot';
import { getWorks, isSearchMode, searchCorpus, searchFacets } from '../../lib/api/client';
import { PAGE, SEARCH } from '../../lib/constants';
import { scopeTokens, toggleGroup, toggleOne, wireCategories } from '../../lib/taxonomySelection';
import type { ScopeToken } from '../../lib/taxonomySelection';
import type { CorpusMatch, SearchFacets as Facets, SearchMode, Work } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { usePaged } from '../../lib/usePaged';
import { useCategoryLabels } from '../../lib/useCategoryLabels';
import { useDomains } from '../../lib/useDomains';
import { countLabel, formatCount } from '../../lib/utils';
import { FilterBar } from '../library/FilterBar';
import { DEFAULT_FILTERS, applyFilters } from '../library/worksFilter';
import type { Filters } from '../library/worksFilter';
import { rollupByDomain } from './facetRollup';
import { FilterPopover } from './FilterPopover';
import { PassageGroups } from './PassageGroups';
import { ResultsFrame } from './ResultsFrame';
import { SearchMap } from './SearchMap';
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
export function ContentScope({
  q,
  initialMode = SEARCH.DEFAULT_MODE,
  onOpenReader,
  filters,
}: ContentScopeProps) {
  const [localMode, setLocalMode] = useState<SearchMode>(initialMode);
  const [localSelected, setLocalSelected] = useState<ReadonlySet<string>>(() => new Set());
  const [localBook, setLocalBook] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);

  const mode = filters ? filters.mode : localMode;
  const selected = filters ? filters.categories : localSelected;
  const book = filters ? filters.book : localBook;
  const setMode = filters ? filters.onMode : setLocalMode;
  const setSelected = filters ? filters.onCategories : setLocalSelected;
  const setBook = filters ? filters.onBook : setLocalBook;

  const resetFilters = useCallback(() => {
    setSelected(new Set());
    setBook('');
  }, [setSelected, setBook]);

  // Skip the reset on this instance's very first render: a controlled `q`
  // can mount with filters already populated — a bookmarked search, or the
  // URL restored by the Reader's "back to catalog" — and those must survive.
  // Only a genuinely NEW query, i.e. q changing after mount, clears the
  // previous query's category/book filters.
  const mountedForQuery = useRef(false);
  useEffect(() => {
    if (mountedForQuery.current) resetFilters();
    mountedForQuery.current = true;
  }, [q, resetFilters]);

  const categories = useMemo(() => wireCategories(selected), [selected]);
  const corpus = usePaged<CorpusMatch>(
    (offset) => searchCorpus(q, { mode, categories, book, limit: PAGE.defaultLimit, offset }),
    [q, mode, categories, book],
  );
  // The distribution depends only on (q, mode): keyed that way, the map and
  // picker stay mounted across selection changes. The selection-scoped fetch
  // feeds only the per-work head counts (the books facet).
  const facetData = useAsync<Facets>(() => searchFacets(q, mode), [q, mode]);
  const scopedFacets = useAsync<Facets | null>(
    () => (categories.length > 0 ? searchFacets(q, mode, categories) : Promise.resolve(null)),
    [q, mode, categories],
  );
  const domains = useDomains();
  const labelOf = useCategoryLabels();

  // The hit window's distinct books, resolved to their real Work records so
  // the library's own era/author/"largest first" filter (worksFilter.ts)
  // applies here too instead of a second, content-scope-only reimplementation.
  const hitUrns = useMemo(() => Array.from(new Set(corpus.items.map((m) => m.urn))), [corpus.items]);
  const worksRes = useAsync<Work[]>(
    () =>
      hitUrns.length
        ? getWorks({ urns: hitUrns, limit: hitUrns.length }).then((p) => p.items)
        : Promise.resolve([]),
    [hitUrns],
  );
  const [workFilters, setWorkFilters] = useState<Filters>({ ...DEFAULT_FILTERS, sort: 'canonical' });
  const filteredWorks = useMemo(
    () => (worksRes.data ? applyFilters(worksRes.data, workFilters) : null),
    [worksRes.data, workFilters],
  );

  const pickMode = (next: SearchMode) => {
    setMode(next);
    resetFilters();
  };
  const facets = facetData.data;
  const taxonomy = domains.data ?? [];
  const rollup = useMemo(
    () => rollupByDomain(taxonomy, facets?.categories ?? []),
    [taxonomy, facets],
  );
  const groups = useMemo(
    () =>
      rollup.domains.map((d) => ({
        id: d.id,
        label: d.label,
        slugs: d.categories.map((c) => c.slug),
      })),
    [rollup],
  );
  const tokens = useMemo(() => scopeTokens(groups, selected, labelOf), [groups, selected, labelOf]);
  const bookCounts = useMemo(
    () => new Map((scopedFacets.data?.books ?? []).map((b) => [b.title, b.count])),
    [scopedFacets.data],
  );

  const toggleCategory = (slug: string) => {
    setSelected(toggleOne(selected, slug));
    setBook('');
  };
  const toggleDomainGroup = (slugs: readonly string[]) => {
    setSelected(toggleGroup(selected, slugs));
    setBook('');
  };
  const removeToken = (token: ScopeToken) => {
    if (token.kind === 'group') {
      const group = groups.find((g) => g.id === token.id);
      if (group) toggleDomainGroup(group.slugs);
      return;
    }
    toggleCategory(token.id);
  };
  const clearCategories = () => {
    setSelected(new Set());
    setBook('');
  };

  const total = corpus.total ?? 0;
  const filtered = selected.size > 0 || Boolean(book);
  const firstLoad = corpus.loading && corpus.items.length === 0;
  const capped = facetData.data !== null && facetData.data.categories.length === 0 && total > 0;

  return (
    <ResultsFrame
      filters={{
        mode,
        labelOf,
        tokens,
        book,
        total,
        onMode: pickMode,
        onRemoveToken: removeToken,
        onShowAll: () => setPickerOpen(true),
        picker:
          facets && facets.categories.length > 0 ? (
            <FilterPopover
              rollup={rollup}
              selected={selected}
              open={pickerOpen}
              onOpenChange={setPickerOpen}
              labelOf={labelOf}
              onToggleGroup={toggleDomainGroup}
              onToggleCategory={toggleCategory}
              onClearCategories={clearCategories}
            />
          ) : null,
        onBook: setBook,
        onClear: resetFilters,
      }}
      worksFilter={
        worksRes.data && worksRes.data.length > 0 ? (
          <FilterBar works={worksRes.data} filters={workFilters} onChange={setWorkFilters} />
        ) : null
      }
      map={
        <>
          {facets ? (
            <SearchMap
              rollup={rollup}
              categoriesCount={facets.categories.length}
              selected={selected}
              labelOf={labelOf}
              onToggleGroup={toggleDomainGroup}
              onToggleCategory={toggleCategory}
            />
          ) : null}
          {capped ? (
            <Text as="p" size="sm" tone="muted">
              The distribution map is unavailable at this scale: the facet scan caps out before it
              can count a match-set this large. Narrow the phrase to see where it lives.
            </Text>
          ) : null}
        </>
      }
      loading={firstLoad}
      loadingLabel="Searching the corpus"
      error={corpus.error ? `Corpus search is unavailable: ${corpus.error.message}` : null}
      empty={
        !corpus.loading && corpus.total !== null && corpus.items.length === 0
          ? filtered
            ? 'No passages match these filters.'
            : `No book passages match “${q}”.`
          : null
      }
      foot={
        corpus.items.length > 0 ? (
          <LoadMoreFoot
            line={`Showing ${formatCount(corpus.items.length)} of ${countLabel(total, 'passage')}`}
            loading={corpus.loading}
            spinnerLabel="Loading more passages"
            hasMore={corpus.hasMore}
            onMore={corpus.more}
          />
        ) : null
      }
    >
      {corpus.items.length > 0 ? (
        <PassageGroups
          items={corpus.items}
          q={q}
          activeBook={book}
          bookCounts={bookCounts}
          filteredWorks={filteredWorks}
          onPickBook={setBook}
          onOpen={(urn, page) => onOpenReader(urn, page, q)}
        />
      ) : null}
    </ResultsFrame>
  );
}
