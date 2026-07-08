import { useCallback, useEffect, useState } from 'react';

import type { SearchScope } from '../lib/api/client';
import { SEARCH_SCOPES } from '../lib/api/client';
import { EMPTY_ROUTE, parseHash } from '../lib/routes';
import type { RouteState } from '../lib/routes';
import { saveReading } from '../lib/reading';
import { recordSearch } from '../lib/searchHistory';
import { useHashRoute } from '../lib/useHashRoute';
import { EMPTY_GRAPH, GraphScreen } from '../features/graph/GraphScreen';
import type { GraphState } from '../features/graph/GraphScreen';
import { HomeScreen } from '../features/home/HomeScreen';
import { LibraryScreen } from '../features/library/LibraryScreen';
import { QuranScreen } from '../features/quran/QuranScreen';
import { ReaderScreen } from '../features/reader/ReaderScreen';
import { SearchResults } from '../features/search/SearchResults';
import { useContentFilters } from '../features/search/ContentScope';
import type { ContentFilters } from '../features/search/ContentScope';
import { DesignSystemScreen } from '../features/design/DesignSystemScreen';
import { ExtractionScreen } from '../features/extraction/ExtractionScreen';
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

/** 'sura' (the Qurʾān reader's in-place sūra filter) only means anything
    alongside a loaded sūra: outside the Qurʾān view it falls back to the app
    default, and a bare '/quran' hash with no explicit scope defaults TO it
    (the reader's default pick), matching the reader's own default. */
const coerceScope = (scope: string, view: NavView): SearchScope => {
  if ((LEGACY_WORKS_SCOPES as readonly string[]).includes(scope)) return 'works';
  if ((SEARCH_SCOPES as readonly string[]).includes(scope)) {
    return scope === 'sura' && view !== 'quran' ? 'content' : (scope as SearchScope);
  }
  return view === 'quran' ? 'sura' : 'content';
};

interface AppContentProps {
  searching: boolean;
  submitted: string;
  scope: SearchScope;
  view: NavView;
  lib: LibScope;
  graph: GraphState;
  setGraph: (next: GraphState) => void;
  quranFocus: { surah: number; aya: number } | null;
  openVerse: (surah: number, aya: number) => void;
  openReader: (urn: string, page?: number, q?: string) => void;
  contentFilters: ContentFilters;
}

/** The shell's child: the search overlay when a query is submitted, otherwise the
    active view. Extracted from App so the router stays under the function size cap. */
function AppContent({
  searching,
  submitted,
  scope,
  view,
  lib,
  graph,
  setGraph,
  quranFocus,
  openVerse,
  openReader,
  contentFilters,
}: AppContentProps) {
  if (searching) {
    return (
      <SearchResults
        query={submitted}
        scope={scope}
        onOpenVerse={openVerse}
        onOpenReader={openReader}
        contentFilters={contentFilters}
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
      {view === 'quran' ? <QuranScreen query={submitted} focus={quranFocus} /> : null}
      {view === 'graph' ? (
        <GraphScreen state={graph} onState={setGraph} onOpenReader={openReader} />
      ) : null}
      {view === 'design' ? <DesignSystemScreen /> : null}
      {view === 'extraction' ? <ExtractionScreen /> : null}
    </>
  );
}

/** State-based router synced to the URL fragment through one useHashRoute bridge
    (routes.ts owns the hash format). Search is driven by the SUBMITTED query, set
    on Enter — never live as you type — so a slow corpus query runs once when you
    finish, not once per word. ``query`` is just the live input text; ``submitted``
    is the single source the SearchResults overlay and the URL read from. The Reader
    is a full-screen takeover bound to a book URN + page; every position it reaches
    is persisted (reading.ts) so the landing page can offer re-entry. The content
    scope's filters (mode/categories/book, useContentFilters) are lifted here too,
    for the same reason: round-tripped through the URL, they survive a Reader visit
    and back, and make the search results page itself bookmarkable at its exact
    filtered state. */
export function App() {
  const initial = parseHash(window.location.hash);
  const [view, setView] = useState<NavView>(initial.view);
  const [query, setQuery] = useState(initial.reading ? '' : initial.query);
  const [submitted, setSubmitted] = useState(initial.reading ? '' : initial.query);
  const [scope, setScope] = useState<SearchScope>(coerceScope(initial.scope, initial.view));
  const [lib, setLib] = useState<LibScope>({ cat: initial.cat, dom: initial.dom });
  const [graph, setGraph] = useState<GraphState>(EMPTY_GRAPH);
  const contentFilters = useContentFilters(initial);
  const [reading, setReading] = useState<Reading | null>(
    initial.reading ? { ...initial.reading } : null,
  );
  const [quranFocus, setQuranFocus] = useState(initial.focus);

  useEffect(() => {
    if (reading) saveReading(reading.urn, reading.page);
  }, [reading]);

  const route: RouteState = reading
    ? {
        ...EMPTY_ROUTE,
        view,
        scope,
        reading: { urn: reading.urn, page: reading.page, query: reading.query },
      }
    : {
        view,
        query: submitted,
        scope,
        cat: lib.cat,
        dom: lib.dom,
        reading: null,
        focus: view === 'quran' ? quranFocus : null,
        ...contentFilters.route,
      };
  const applyRoute = useCallback(
    (next: RouteState) => {
      setView(next.view);
      setScope(coerceScope(next.scope, next.view));
      setQuery(next.reading ? '' : next.query);
      setSubmitted(next.reading ? '' : next.query);
      setLib({ cat: next.cat, dom: next.dom });
      setReading(next.reading ? { ...next.reading } : null);
      setQuranFocus(next.focus);
      contentFilters.restore(next);
    },
    [contentFilters.restore],
  );
  useHashRoute(route, applyRoute);

  // A Qurʾān citation in the reader closes the takeover and opens the Qurʾān
  // view focused on that verse.
  const openVerse = (surah: number, aya: number) => {
    setReading(null);
    setView('quran');
    setQuery('');
    setSubmitted('');
    setScope('sura');
    setQuranFocus({ surah, aya });
  };

  if (reading) {
    return (
      <ReaderScreen
        urn={reading.urn}
        page={reading.page}
        initialQuery={reading.query}
        onPage={(p) => setReading((r) => (r ? { ...r, page: p } : r))}
        onVolume={(u) => setReading((r) => (r ? { ...r, urn: u, page: 1 } : r))}
        onCite={openVerse}
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
    setQuranFocus(null);
    contentFilters.reset();
    // The Qurʾān reader's sūra filter is the default pick on landing there;
    // leaving it behind a scope with no meaning outside the reader.
    if (v === 'quran') setScope('sura');
    else if (scope === 'sura') setScope('content');
  };
  // Typing only updates the field; clearing it closes the results. Enter commits.
  const onQuery = (next: string) => {
    setQuery(next);
    if (!next.trim()) setSubmitted('');
  };
  const onSearch = () => {
    const trimmed = query.trim();
    setSubmitted(trimmed);
    // The sūra filter is a transient in-page state, never a resumable global
    // search: recording it would offer "recent searches" with no scope to
    // pick back up outside the sūra that was open at the time.
    if (scope !== 'sura') recordSearch(trimmed, scope);
  };
  // A result can launch a new search (a Qurʾān verse opens its reference): set
  // scope + query as state and let useHashRoute mirror it to the URL. Also the
  // header's recent-searches dropdown re-runs a past query+scope through this.
  const runSearch = (next: string, nextScope: SearchScope) => {
    setScope(nextScope);
    setQuery(next);
    setSubmitted(next);
    recordSearch(next, nextScope);
  };
  // The sūra scope filters the open sūra in place instead of opening the
  // overlay, and the field's clear button restores the unfiltered page; every
  // other scope opens the overlay same as any other view.
  const searching = submitted.trim().length > 0 && scope !== 'sura';

  return (
    <AppShell
      active={view}
      query={query}
      scope={scope}
      onNav={onNav}
      onQuery={onQuery}
      onSearch={onSearch}
      onScope={setScope}
      onClear={() => onQuery('')}
      onPickHistory={runSearch}
    >
      <AppContent
        searching={searching}
        submitted={submitted}
        scope={scope}
        view={view}
        lib={lib}
        graph={graph}
        setGraph={setGraph}
        quranFocus={quranFocus}
        openVerse={openVerse}
        openReader={openReader}
        contentFilters={contentFilters.filters}
      />
    </AppShell>
  );
}
