import { useCallback, useMemo, useState } from 'react';

import { Spinner, Text } from '../../lib/design-system';
import { getDomains, getWorks } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import type { Domain, Page, Work } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { CorpusOverview } from './CorpusOverview';
import { FihristRail } from './FihristRail';
import { WorksPane } from './WorksPane';
import { domainLabel, domainLabelAr, labelArOf, labelOf } from './lib';
import type { TraditionLens } from './lib';
import '../screens.css';
import './LibraryScreen.css';

const PER_PAGE = PAGE.defaultLimit;

/** Rail state + handlers, kept together so every entry point shares one scope
    discipline. Browsing (a category, a domain, the lens) and searching (the rail
    filter) are mutually exclusive: picking a scope clears the search, and typing
    a search clears the scope. */
function useScope(domainOfCat: Map<string, string>) {
  const [cat, setCat] = useState('');
  const [dom, setDom] = useState('');
  const [lens, setLens] = useState<TraditionLens>('all');
  const [filter, setFilter] = useState('');
  const [openDomains, setOpenDomains] = useState<Set<string>>(() => new Set());
  const [page, setPage] = useState(1);

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

function useWorks(cat: string, dom: string, lens: TraditionLens, page: number, filter: string) {
  return useAsync<Page<Work> | null>(() => {
    const q = filter.trim();
    if (!q && !cat && !dom) return Promise.resolve(null);
    return getWorks({
      q,
      category: q ? '' : cat,
      domain: q ? '' : dom,
      tradition: lens === 'all' ? '' : lens,
      limit: PER_PAGE,
      offset: (page - 1) * PER_PAGE,
    });
  }, [cat, dom, lens, page, filter]);
}

export interface LibraryScreenProps {
  onOpenReader: (urn: string) => void;
}

/** The Library as a two-column reading room: a sticky Fihrist rail (the whole
    taxonomy, grouped, with a works search) and a results pane that swaps in place
    between the corpus overview and a volume-folded work list. */
export function LibraryScreen({ onOpenReader }: LibraryScreenProps) {
  const domains = useAsync<Domain[]>(() => getDomains(), []);
  const list = domains.data ?? [];
  const domainOfCat = useMemo(() => {
    const map = new Map<string, string>();
    for (const d of list) for (const c of d.categories) map.set(c.slug, d.id);
    return map;
  }, [list]);
  const sc = useScope(domainOfCat);
  const works = useWorks(sc.cat, sc.dom, sc.lens, sc.page, sc.filter);

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
  const scopeLabel = searching
    ? `“${sc.filter.trim()}”`
    : sc.cat
      ? labelOf(list, sc.cat)
      : domainLabel(list, sc.dom);
  const scopeLabelAr = searching
    ? 'بحث'
    : sc.cat
      ? labelArOf(list, sc.cat)
      : domainLabelAr(list, sc.dom);
  const breadcrumb = searching
    ? 'Library / Search'
    : sc.cat
      ? `Library / ${domainLabel(list, parentDom)} / ${scopeLabel}`
      : `Library / ${scopeLabel}`;

  return (
    <section className="library">
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
          {sc.scoped ? (
            <WorksPane
              breadcrumb={breadcrumb}
              scopeLabel={scopeLabel}
              scopeLabelAr={scopeLabelAr}
              works={works.data ?? null}
              loading={works.loading}
              error={works.error}
              page={sc.page}
              perPage={PER_PAGE}
              labelFor={(slug) => labelOf(list, slug)}
              onPage={sc.setPage}
              onOpen={onOpenReader}
            />
          ) : (
            <CorpusOverview domains={list} onPickDomain={sc.pickDomain} />
          )}
        </div>
      </div>
    </section>
  );
}
