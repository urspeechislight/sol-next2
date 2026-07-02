import { useCallback, useEffect, useState } from 'react';

import type { SearchScope } from '../lib/api/client';
import { SEARCH_SCOPES } from '../lib/api/client';
import { parseHash } from '../lib/routes';
import type { RouteState } from '../lib/routes';
import { saveReading } from '../lib/reading';
import { useHashRoute } from '../lib/useHashRoute';
import { GraphScreen } from '../features/graph/GraphScreen';
import { HomeScreen } from '../features/home/HomeScreen';
import { LibraryScreen } from '../features/library/LibraryScreen';
import { QuranScreen } from '../features/quran/QuranScreen';
import { ReaderScreen } from '../features/reader/ReaderScreen';
import { SearchResults } from '../features/search/SearchResults';
import { DesignSystemScreen } from '../features/design/DesignSystemScreen';
import '../lib/design-system/tokens.css';
import '../lib/design-system/base.css';
import { AppShell } from './shell/AppShell';
import type { NavView } from './shell/nav';

interface Reading {
  urn: string;
  page: number;
  query: string;
}

/** Library deep-link scope: at most one of category / domain is set. */
interface LibScope {
  cat: string;
  dom: string;
}

/** The catalog scopes that predated the folded works search; an old URL's
    scope lands on its one successor instead of silently becoming content. */
const LEGACY_WORKS_SCOPES = ['title', 'author', 'book'] as const;

const coerceScope = (scope: string): SearchScope => {
  if ((LEGACY_WORKS_SCOPES as readonly string[]).includes(scope)) return 'works';
  return (SEARCH_SCOPES as readonly string[]).includes(scope) ? (scope as SearchScope) : 'content';
};

interface AppContentProps {
  searching: boolean;
  submitted: string;
  scope: SearchScope;
  view: NavView;
  lib: LibScope;
  runSearch: (next: string, nextScope: SearchScope) => void;
  openReader: (urn: string, page?: number, q?: string) => void;
}

/** The shell's child: the search overlay when a query is submitted, otherwise the
    active view. Extracted from App so the router stays under the function size cap. */
function AppContent({
  searching,
  submitted,
  scope,
  view,
  lib,
  runSearch,
  openReader,
}: AppContentProps) {
  if (searching) {
    return (
      <SearchResults
        query={submitted}
        scope={scope}
        onSearch={runSearch}
        onOpenReader={openReader}
      />
    );
  }
  return (
    <>
      {view === 'home' ? <HomeScreen onOpenReader={openReader} /> : null}
      {view === 'library' ? (
        <LibraryScreen
          key={`${lib.cat}|${lib.dom}`}
          initialCategory={lib.cat}
          initialDomain={lib.dom}
          onOpenReader={openReader}
        />
      ) : null}
      {view === 'quran' ? <QuranScreen query={submitted} /> : null}
      {view === 'graph' ? <GraphScreen /> : null}
      {view === 'design' ? <DesignSystemScreen /> : null}
    </>
  );
}

/** State-based router synced to the URL fragment through one useHashRoute bridge
    (routes.ts owns the hash format). Search is driven by the SUBMITTED query, set
    on Enter — never live as you type — so a slow corpus query runs once when you
    finish, not once per word. ``query`` is just the live input text; ``submitted``
    is the single source the SearchResults overlay and the URL read from. The Reader
    is a full-screen takeover bound to a book URN + page; every position it reaches
    is persisted (reading.ts) so the landing page can offer re-entry. */
export function App() {
  const initial = parseHash(window.location.hash);
  const [view, setView] = useState<NavView>(initial.view);
  const [query, setQuery] = useState(initial.reading ? '' : initial.query);
  const [submitted, setSubmitted] = useState(initial.reading ? '' : initial.query);
  const [scope, setScope] = useState<SearchScope>(coerceScope(initial.scope));
  const [lib, setLib] = useState<LibScope>({ cat: initial.cat, dom: initial.dom });
  const [reading, setReading] = useState<Reading | null>(
    initial.reading ? { ...initial.reading, query: '' } : null,
  );

  useEffect(() => {
    if (reading) saveReading(reading.urn, reading.page);
  }, [reading]);

  const route: RouteState = reading
    ? {
        view,
        query: '',
        scope,
        cat: '',
        dom: '',
        reading: { urn: reading.urn, page: reading.page },
      }
    : { view, query: submitted, scope, cat: lib.cat, dom: lib.dom, reading: null };
  const applyRoute = useCallback((next: RouteState) => {
    setView(next.view);
    setScope(coerceScope(next.scope));
    setQuery(next.reading ? '' : next.query);
    setSubmitted(next.reading ? '' : next.query);
    setLib({ cat: next.cat, dom: next.dom });
    setReading(next.reading ? { ...next.reading, query: '' } : null);
  }, []);
  useHashRoute(route, applyRoute);

  if (reading) {
    return (
      <ReaderScreen
        urn={reading.urn}
        page={reading.page}
        initialQuery={reading.query}
        onPage={(p) => setReading((r) => (r ? { ...r, page: p } : r))}
        onVolume={(u) => setReading((r) => (r ? { ...r, urn: u, page: 1 } : r))}
        onBack={() => setReading(null)}
      />
    );
  }

  const openReader = (urn: string, page = 1, q = '') => setReading({ urn, page, query: q });
  const onNav = (v: NavView) => {
    setView(v);
    setQuery('');
    setSubmitted('');
    setLib({ cat: '', dom: '' });
  };
  // Typing only updates the field; clearing it closes the results. Enter commits.
  const onQuery = (next: string) => {
    setQuery(next);
    if (!next.trim()) setSubmitted('');
  };
  const onSearch = () => setSubmitted(query.trim());
  // A result can launch a new search (a Qurʾān verse opens its reference): set
  // scope + query as state and let useHashRoute mirror it to the URL.
  const runSearch = (next: string, nextScope: SearchScope) => {
    setScope(nextScope);
    setQuery(next);
    setSubmitted(next);
  };
  // On the Qurʾān page the header search is sūra-scoped: the submitted term
  // filters the open sūra in place instead of opening the overlay, and the
  // field's clear button restores the unfiltered page.
  const searching = submitted.trim().length > 0 && view !== 'quran';

  return (
    <AppShell
      active={view}
      query={query}
      scope={scope}
      scopeLock={view === 'quran' ? 'this sūra' : undefined}
      onNav={onNav}
      onQuery={onQuery}
      onSearch={onSearch}
      onScope={setScope}
      onClear={() => onQuery('')}
    >
      <AppContent
        searching={searching}
        submitted={submitted}
        scope={scope}
        view={view}
        lib={lib}
        runSearch={runSearch}
        openReader={openReader}
      />
    </AppShell>
  );
}
