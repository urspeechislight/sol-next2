import { useCallback, useState } from 'react';

import type { SearchScope } from '../lib/api/client';
import { SEARCH_SCOPES } from '../lib/api/client';
import { parseHash } from '../lib/routes';
import type { RouteState } from '../lib/routes';
import { useHashRoute } from '../lib/useHashRoute';
import { DailyScreen } from '../features/daily/DailyScreen';
import { GraphScreen } from '../features/graph/GraphScreen';
import { HomeScreen } from '../features/home/HomeScreen';
import { LibraryScreen } from '../features/library/LibraryScreen';
import { ReaderScreen } from '../features/reader/ReaderScreen';
import { SearchResults } from '../features/search/SearchResults';
import { DesignSystemScreen } from '../features/design/DesignSystemScreen';
import '../lib/design-system/tokens.css';
import '../lib/design-system/base.css';
import { AppShell } from './shell/AppShell';
import type { NavView } from './shell/nav';

// The book Home's "start reading" opens by default.
const DEFAULT_URN = 'sY-50TSO';

interface Reading {
  urn: string;
  page: number;
  query: string;
}

const coerceScope = (scope: string): SearchScope =>
  (SEARCH_SCOPES as readonly string[]).includes(scope) ? (scope as SearchScope) : 'content';

interface AppContentProps {
  searching: boolean;
  submitted: string;
  scope: SearchScope;
  view: NavView;
  runSearch: (next: string, nextScope: SearchScope) => void;
  openReader: (urn: string, page?: number, q?: string) => void;
  onNav: (v: NavView) => void;
}

/** The shell's child: the search overlay when a query is submitted, otherwise the
    active view. Extracted from App so the router stays under the function size cap. */
function AppContent({
  searching,
  submitted,
  scope,
  view,
  runSearch,
  openReader,
  onNav,
}: AppContentProps) {
  if (searching) {
    return (
      <SearchResults query={submitted} scope={scope} onSearch={runSearch} onOpenReader={openReader} />
    );
  }
  return (
    <>
      {view === 'home' ? (
        <HomeScreen onNav={onNav} onOpenReader={() => openReader(DEFAULT_URN)} />
      ) : null}
      {view === 'library' ? <LibraryScreen onOpenReader={(urn) => openReader(urn)} /> : null}
      {view === 'daily' ? <DailyScreen onOpenReader={(urn) => openReader(urn)} /> : null}
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
    is a full-screen takeover bound to a book URN + page. */
export function App() {
  const initial = parseHash(window.location.hash);
  const [view, setView] = useState<NavView>(initial.view);
  const [query, setQuery] = useState(initial.reading ? '' : initial.query);
  const [submitted, setSubmitted] = useState(initial.reading ? '' : initial.query);
  const [scope, setScope] = useState<SearchScope>(coerceScope(initial.scope));
  const [reading, setReading] = useState<Reading | null>(
    initial.reading ? { ...initial.reading, query: '' } : null,
  );

  const route: RouteState = reading
    ? { view, query: '', scope, reading: { urn: reading.urn, page: reading.page } }
    : { view, query: submitted, scope, reading: null };
  const applyRoute = useCallback((next: RouteState) => {
    setView(next.view);
    setScope(coerceScope(next.scope));
    setQuery(next.reading ? '' : next.query);
    setSubmitted(next.reading ? '' : next.query);
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
        onBack={() => setReading(null)}
      />
    );
  }

  const openReader = (urn: string, page = 1, q = '') => setReading({ urn, page, query: q });
  const onNav = (v: NavView) => {
    setView(v);
    setQuery('');
    setSubmitted('');
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
  const searching = submitted.trim().length > 0;

  return (
    <AppShell
      active={view}
      query={query}
      scope={scope}
      onNav={onNav}
      onQuery={onQuery}
      onSearch={onSearch}
      onScope={setScope}
    >
      <AppContent
        searching={searching}
        submitted={submitted}
        scope={scope}
        view={view}
        runSearch={runSearch}
        openReader={openReader}
        onNav={onNav}
      />
    </AppShell>
  );
}
