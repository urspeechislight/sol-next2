import { useCallback, useEffect, useMemo, useState } from 'react';

import { PageGlow, Spinner, Text } from '../../lib/design-system';
import { getWorks } from '../../lib/api/client';
import { LIBRARY, PAGE } from '../../lib/constants';
import type { Page, Work } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { useDomains } from '../../lib/useDomains';
import { CategoryPane } from './CategoryPane';
import { CorpusOverview } from './CorpusOverview';
import { DomainPane } from './DomainPane';
import { FihristRail } from './FihristRail';
import { WorksPane } from './WorksPane';
import { domainLabel, labelArOf, labelOf } from './lib';
import type { TraditionLens } from './lib';
import '../screens.css';
import './LibraryScreen.css';

const PER_PAGE = PAGE.defaultLimit;

/** Rail state + handlers, kept together so every entry point shares one scope
    discipline. Browsing (a category, a domain, the lens) and searching (the rail
    filter) are mutually exclusive: picking a scope clears the search, and typing
    a search clears the scope. */
function useScope(domainOfCat: Map<string, string>, initialCat = '', initialDom = '') {
  const [cat, setCat] = useState(initialCat);
  const [dom, setDom] = useState(initialDom);
  const [lens, setLens] = useState<TraditionLens>('all');
  const [filter, setFilter] = useState('');
  const [openDomains, setOpenDomains] = useState<Set<string>>(
    () => new Set(initialDom ? [initialDom] : []),
  );
  const [page, setPage] = useState(1);

  // A deep-linked category expands its owning domain in the rail once the
  // taxonomy has loaded (the map is empty on the first render).
  useEffect(() => {
    if (!cat) return;
    const owner = domainOfCat.get(cat);
    if (owner) setOpenDomains((s) => (s.has(owner) ? s : new Set(s).add(owner)));
  }, [cat, domainOfCat]);

  const pickCategory = useCallback(
    (slug: string) => {
      setCat(slug);
      setDom('');
      setFilter('');
      setPage(1);
      const owner = domainOfCat.get(slug);
      if (owner) setOpenDomains((s) => new Set(s).add(owner));
    },
    [domainOfCat],
  );
  const pickDomain = useCallback((id: string) => {
    setDom(id);
    setCat('');
    setFilter('');
    setPage(1);
    setOpenDomains((s) => new Set(s).add(id));
  }, []);
  const toggleDomain = useCallback((id: string) => {
    setOpenDomains((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
    setDom(id);
    setCat('');
    setFilter('');
    setPage(1);
  }, []);
  const changeLens = useCallback((next: TraditionLens) => {
    setLens(next);
    setCat('');
    setDom('');
    setFilter('');
    setPage(1);
  }, []);
  const changeFilter = useCallback((value: string) => {
    setFilter(value);
    setCat('');
    setDom('');
    setPage(1);
  }, []);
  const reset = useCallback(() => {
    setCat('');
    setDom('');
    setFilter('');
    setPage(1);
  }, []);

  return {
    cat,
    dom,
    lens,
    filter,
    openDomains,
    page,
    scoped: Boolean(cat || dom || filter.trim()),
    setPage,
    changeFilter,
    pickCategory,
    pickDomain,
    toggleDomain,
    changeLens,
    reset,
  };
}

function useSearchWorks(lens: TraditionLens, page: number, filter: string) {
  return useAsync<Page<Work> | null>(() => {
    const q = filter.trim();
    if (!q) return Promise.resolve(null);
    return getWorks({
      q,
      tradition: lens === 'all' ? '' : lens,
      limit: PER_PAGE,
      offset: (page - 1) * PER_PAGE,
    });
  }, [lens, page, filter]);
}

/** Assemble a whole category (paged fetches of PAGE.facetLimit) so the pane can
    shelve landmarks and group by era. Bounded by LIBRARY.categoryMax; the pane
    says so when a scope is larger. */
function useCategoryWorks(cat: string, lens: TraditionLens) {
  return useAsync<{ items: Work[]; total: number } | null>(async () => {
    if (!cat) return null;
    const tradition = lens === 'all' ? '' : lens;
    const first = await getWorks({ category: cat, tradition, limit: PAGE.facetLimit, offset: 0 });
    const items = [...first.items];
    while (items.length < first.total && items.length < LIBRARY.categoryMax) {
      const next = await getWorks({
        category: cat,
        tradition,
        limit: PAGE.facetLimit,
        offset: items.length,
      });
      if (next.items.length === 0) break;
      items.push(...next.items);
    }
    return { items, total: first.total };
  }, [cat, lens]);
}

export interface LibraryScreenProps {
  onOpenReader: (urn: string) => void;
  /** Deep-link scope from the URL / home hero: at most one of the two. */
  initialCategory?: string;
  initialDomain?: string;
}

/** The Library as a two-column reading room with progressive depth: the
    corpus overview (domain cards), a domain as category tiles, a category as
    a landmarks shelf over era-grouped works, and the rail search as a flat
    paged result list. Each step narrows; nothing dumps the whole scope. */
export function LibraryScreen({
  onOpenReader,
  initialCategory = '',
  initialDomain = '',
}: LibraryScreenProps) {
  const domains = useDomains();
  const list = domains.data ?? [];
  const domainOfCat = useMemo(() => {
    const map = new Map<string, string>();
    for (const d of list) for (const c of d.categories) map.set(c.slug, d.id);
    return map;
  }, [list]);
  const sc = useScope(domainOfCat, initialCategory, initialDomain);
  const search = useSearchWorks(sc.lens, sc.page, sc.filter);
  const category = useCategoryWorks(sc.cat, sc.lens);

  if (domains.loading) {
    return (
      <div className="library__loading">
        <Spinner label="Loading the library" />
      </div>
    );
  }
  if (domains.error) {
    return (
      <Text as="p" size="sm" tone="danger">
        Could not load the taxonomy: {domains.error.message}
      </Text>
    );
  }

  const searching = sc.filter.trim().length > 0;
  const parentDom = sc.cat ? (domainOfCat.get(sc.cat) ?? '') : sc.dom;
  const activeDomain = sc.dom ? (list.find((d) => d.id === sc.dom) ?? null) : null;

  return (
    <section className="library">
      <PageGlow />
      <div className="library__grid">
        <FihristRail
          domains={list}
          lens={sc.lens}
          filter={sc.filter}
          openDomains={sc.openDomains}
          activeCat={sc.cat}
          activeDomain={sc.dom}
          scoped={sc.scoped}
          onLens={sc.changeLens}
          onFilter={sc.changeFilter}
          onToggleDomain={sc.toggleDomain}
          onPickCategory={sc.pickCategory}
          onReset={sc.reset}
        />
        <div className="library__pane">
          {searching ? (
            <WorksPane
              breadcrumb="Library / Search"
              scopeLabel={`“${sc.filter.trim()}”`}
              scopeLabelAr="بحث"
              works={search.data ?? null}
              loading={search.loading}
              error={search.error}
              page={sc.page}
              perPage={PER_PAGE}
              labelFor={(slug) => labelOf(list, slug)}
              onPage={sc.setPage}
              onOpen={onOpenReader}
            />
          ) : sc.cat ? (
            <CategoryPane
              breadcrumb={`Library / ${domainLabel(list, parentDom)} / ${labelOf(list, sc.cat)}`}
              scopeLabel={labelOf(list, sc.cat)}
              scopeLabelAr={labelArOf(list, sc.cat)}
              works={category.data?.items ?? null}
              total={category.data?.total ?? 0}
              loading={category.loading}
              error={category.error}
              onOpen={onOpenReader}
            />
          ) : activeDomain ? (
            <DomainPane
              domain={activeDomain}
              lens={sc.lens}
              onPickCategory={sc.pickCategory}
              onOpen={onOpenReader}
            />
          ) : (
            <CorpusOverview domains={list} onPickDomain={sc.pickDomain} onOpen={onOpenReader} />
          )}
        </div>
      </div>
    </section>
  );
}
