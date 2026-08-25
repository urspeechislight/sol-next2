import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { Text } from '../../lib/design-system';
import { LoadMoreFoot } from '../../lib/LoadMoreFoot';
import { getWorks } from '../../lib/api/client';
import { PAGE, SEARCH } from '../../lib/constants';
import { scopeTokens, toggleGroup, toggleOne, wireCategories } from '../../lib/taxonomySelection';
import type { ScopeToken } from '../../lib/taxonomySelection';
import type { CorpusMatch, Page, SearchFacets as Facets, SearchMode, Work } from '../../lib/types';
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
import type { ContentFilters } from './ContentScope';
import './SearchResults.css';

/** The two fetchers a corpus-results scope supplies: one page of matches and
    the drill-down facets, both already scoped by mode/categories/book. */
export interface CorpusFetcher {
  matches: (
    q: string,
    scope: { mode: SearchMode; categories: string[]; book: string; limit: number; offset: number },
  ) => Promise<Page<CorpusMatch>>;
  facets: (q: string, mode: SearchMode, categories: string[]) => Promise<Facets>;
}

export interface CorpusResultsProps {
  q: string;
  onOpenReader: (urn: string, page: number, query: string) => void;
  /** The scope's fetchers: content passes the corpus engine; semantic passes
      the LLM-planned endpoints. The results machinery is identical. */
  fetcher: CorpusFetcher;
  /** Controlled filters for the top-level search (bookmarkable, survives the
      Reader round trip). Omitted by embedded uses, which keep local state. */
  filters?: ContentFilters;
  /** Locks the match-mode control off (the planner fixes broad mode). */
  lockMode?: boolean;
  /** Initial local match mode for uncontrolled uses (the Qur'an scope passes
      broad); ignored when `filters` or `lockMode` governs the mode. */
  initialMode?: SearchMode;
  /** Loading announcement; defaults fit the content scope. */
  loadingLabel?: string;
}

/** The one corpus results engine: distribution map, taxonomy picker + tokens,
    works FilterBar, book drill-in, honest paging. Content and semantic are
    two fetcher bindings over this — there is no second results shape. */
export function CorpusResults({
  q,
  onOpenReader,
  fetcher,
  filters,
  lockMode = false,
  initialMode = SEARCH.DEFAULT_MODE,
  loadingLabel = 'Searching the corpus',
}: CorpusResultsProps) {
  const [localMode, setLocalMode] = useState<SearchMode>(initialMode);
  const [localSelected, setLocalSelected] = useState<ReadonlySet<string>>(() => new Set());
  const [localBook, setLocalBook] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);

  const mode = lockMode ? SEARCH.DEFAULT_MODE : filters ? filters.mode : localMode;
  const selected = filters ? filters.categories : localSelected;
  const book = filters ? filters.book : localBook;
  const setMode = lockMode ? () => {} : filters ? filters.onMode : setLocalMode;
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
    (offset) =>
      fetcher.matches(q, {
        mode,
        categories,
        book,
        limit: PAGE.defaultLimit,
        offset,
      }),
    [q, mode, categories, book],
  );
  // The distribution depends only on (q, mode): keyed that way, the map and
  // picker stay mounted across selection changes. The selection-scoped fetch
  // feeds only the per-work head counts (the books facet).
  const facetData = useAsync<Facets>(() => fetcher.facets(q, mode, []), [q, mode]);
  const scopedFacets = useAsync<Facets | null>(
    () => (categories.length > 0 ? fetcher.facets(q, mode, categories) : Promise.resolve(null)),
    [q, mode, categories],
  );
  const domains = useDomains();
  const labelOf = useCategoryLabels();

  // The hit window's distinct books, resolved to their real Work records so
  // the library's own era/author/"largest first" filter (worksFilter.ts)
  // applies here too instead of a second, content-scope-only reimplementation.
  const hitUrns = useMemo(
    () => Array.from(new Set(corpus.items.map((m) => m.urn))),
    [corpus.items],
  );
  const worksRes = useAsync<Work[]>(
    () =>
      hitUrns.length
        ? getWorks({ urns: hitUrns, limit: hitUrns.length }).then((p) => p.items)
        : Promise.resolve([]),
    [hitUrns],
  );
  const [workFilters, setWorkFilters] = useState<Filters>({
    ...DEFAULT_FILTERS,
    sort: 'canonical',
  });
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
        onMode: lockMode ? undefined : pickMode,
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
      loadingLabel={loadingLabel}
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
