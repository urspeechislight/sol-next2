import { useCallback, useEffect, useMemo, useState } from 'react';

import { Button, Spinner, Text } from '../../lib/design-system';
import { searchCorpus, searchFacets } from '../../lib/api/client';
import type { SearchMode } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import { scopeTokens, toggleGroup, toggleOne, wireCategories } from '../../lib/taxonomySelection';
import type { ScopeToken } from '../../lib/taxonomySelection';
import type { CorpusMatch, SearchFacets as Facets } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { usePaged } from '../../lib/usePaged';
import { useCategoryLabels } from '../../lib/useCategoryLabels';
import { useDomains } from '../../lib/useDomains';
import { countLabel } from '../library/lib';
import { rollupByDomain } from './facetRollup';
import { FilterPopover } from './FilterPopover';
import { PassageGroups } from './PassageGroups';
import { ResultsFrame } from './ResultsFrame';
import { SearchMap } from './SearchMap';
import './SearchResults.css';

export interface ContentScopeProps {
  q: string;
  initialMode?: SearchMode;
  onOpenReader: (urn: string, page: number, query: string) => void;
}

/** Full-text content search as a concordance page over ONE selection set:
    the distribution map's domain/category chips and the funnel popover are
    two views of the same set of category slugs (multi-select, OR'd
    server-side as repeated params), the toolbar shows the collapsed tokens
    and the union count, and the stream is the work-grouped anthology. Above
    the facet scan cap the map and picker are absent and SAY so. The Qurʾan
    scope reuses this with the resolved verse as `q` and broad mode. */
export function ContentScope({ q, initialMode = 'exact', onOpenReader }: ContentScopeProps) {
  const [mode, setMode] = useState<SearchMode>(initialMode);
  const [selected, setSelected] = useState<ReadonlySet<string>>(() => new Set());
  const [book, setBook] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);

  const resetFilters = useCallback(() => {
    setSelected(new Set());
    setBook('');
  }, []);

  useEffect(() => resetFilters(), [q, resetFilters]);

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
    setSelected((s) => toggleOne(s, slug));
    setBook('');
  };
  const toggleDomainGroup = (slugs: readonly string[]) => {
    setSelected((s) => toggleGroup(s, slugs));
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
          <footer className="scr__foot">
            <Text size="xs" tone="faint" font="mono">
              Showing {corpus.items.length.toLocaleString()} of {countLabel(total, 'passage')}
            </Text>
            {corpus.loading ? <Spinner label="Loading more passages" /> : null}
            {!corpus.loading && corpus.hasMore ? (
              <Button variant="secondary" size="sm" onClick={corpus.more}>
                Show more
              </Button>
            ) : null}
          </footer>
        ) : null
      }
    >
      {corpus.items.length > 0 ? (
        <PassageGroups
          items={corpus.items}
          q={q}
          activeBook={book}
          bookCounts={bookCounts}
          onPickBook={setBook}
          onOpen={(urn, page) => onOpenReader(urn, page, q)}
        />
      ) : null}
    </ResultsFrame>
  );
}
