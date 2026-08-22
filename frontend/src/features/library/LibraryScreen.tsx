import { useCallback, useEffect, useMemo, useState } from 'react';

import { PageGlow, Spinner, Text } from '../../lib/design-system';
import { useAsync } from '../../lib/useAsync';
import { useDomains } from '../../lib/useDomains';
import { CategoryPane } from './CategoryPane';
import { CorpusOverview } from './CorpusOverview';
import { DomainPane } from './DomainPane';
import { FihristRail } from './FihristRail';
import { ScopeHead } from './ScopeHead';
import { WorksQueryResults } from './WorksQueryResults';
import { assembleWorks, domainLabel, labelArOf, labelOf } from './lib';
import type { AssembledWorks, TraditionLens } from './lib';
import '../screens.css';
import './LibraryScreen.css';

/** Rail state + handlers, kept together so every entry point shares one scope
    discipline. Browsing (a category, a domain, the lens) and searching (the
    rail filter) are mutually exclusive: picking a scope clears the search,
    and typing a search clears the scope. Selecting and expanding are separate
    acts with one consequence each: a domain's name selects it (the pane
    changes), only its chevron folds the rail group open or closed. */
function useScope(domainOfCat: Map<string, string>, initialCat = '', initialDom = '') {
  const [cat, setCat] = useState(initialCat);
  const [dom, setDom] = useState(initialDom);
  const [lens, setLens] = useState<TraditionLens>('all');
  const [filter, setFilter] = useState('');
  const [openDomains, setOpenDomains] = useState<Set<string>>(() => new Set());

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
      const owner = domainOfCat.get(slug);
      if (owner) setOpenDomains((s) => new Set(s).add(owner));
    },
    [domainOfCat],
  );
  const pickDomain = useCallback((id: string) => {
    setDom(id);
    setCat('');
    setFilter('');
  }, []);
  const toggleDomain = useCallback((id: string) => {
    setOpenDomains((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);
  const changeLens = useCallback((next: TraditionLens) => {
    setLens(next);
    setCat('');
    setDom('');
    setFilter('');
  }, []);
  const changeFilter = useCallback((value: string) => {
    setFilter(value);
    setCat('');
    setDom('');
  }, []);
  const reset = useCallback(() => {
    setCat('');
    setDom('');
    setFilter('');
  }, []);

  return {
    cat,
    dom,
    lens,
    filter,
    openDomains,
    scoped: Boolean(cat || dom || filter.trim()),
    changeFilter,
    pickCategory,
    pickDomain,
    toggleDomain,
    changeLens,
    reset,
  };
}

/** Assemble a whole category through the shared assembleWorks loop (lib.ts),
    so the pane can filter and section it truthfully. */
function useCategoryWorks(cat: string, lens: TraditionLens) {
  return useAsync<AssembledWorks | null>(async () => {
    if (!cat) return null;
    const tradition = lens === 'all' ? '' : lens;
    return assembleWorks({ category: cat, tradition });
  }, [cat, lens]);
}

export interface LibraryScreenProps {
  onOpenReader: (urn: string, page?: number) => void;
  /** Deep-link scope from the URL / home hero: at most one of the two. */
  initialCategory?: string;
  initialDomain?: string;
}

/** The Library as a two-column reading room with progressive depth: the
    corpus overview (domain contents rows), a domain as its foundational
    shelf plus the schools spread (each category as a section of its leading
    works, never the rail's index repeated), a category as one honest
    filtered list, and the rail search as the same canonical-ranked works
    results the header's Works scope uses. Each step narrows; nothing dumps
    the whole scope and nothing is silently capped. */
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
          onSelectDomain={sc.pickDomain}
          onToggleDomain={sc.toggleDomain}
          onPickCategory={sc.pickCategory}
          onReset={sc.reset}
        />
        <div className="library__pane">
          {searching ? (
            <section className="works">
              <ScopeHead
                breadcrumb="Library / Search"
                labelAr="بحث"
                line={`Results for “${sc.filter.trim()}”`}
              />
              <WorksQueryResults
                q={sc.filter}
                tradition={sc.lens === 'all' ? '' : sc.lens}
                onOpen={onOpenReader}
              />
            </section>
          ) : sc.cat ? (
            <CategoryPane
              breadcrumb={`Library / ${domainLabel(list, parentDom)} / ${labelOf(list, sc.cat)}`}
              scopeLabel={labelOf(list, sc.cat)}
              scopeLabelAr={labelArOf(list, sc.cat)}
              category={sc.cat}
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
            <CorpusOverview domains={list} lens={sc.lens} onPickDomain={sc.pickDomain} />
          )}
        </div>
      </div>
    </section>
  );
}
