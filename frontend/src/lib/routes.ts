// routes.ts:SSOT for path / URL constants: API endpoints, app routes, asset
// URLs. CENTRAL-006 requires frontend path literals to live here, never inline
// in components, the client, or the vite proxy config.

import { SEARCH } from './constants';
import { fromBase64Url, toBase64Url } from './utils';

export const API = {
  BASE: '/api',
  RIJAL: '/rijal',
  PERSON: '/person',
  BOOKS: '/books',
  WORKS: '/works',
  DOMAINS: '/domains',
  DAILY: '/daily',
  ALMANAC: '/almanac',
  TOC: '/toc',
  PAGES: '/pages',
  VOLUMES: '/volumes',
  CITATIONS: '/citations',
  SEARCH: '/search',
  FACETS: '/facets',
  QURAN: '/quran',
  DEV_EXTRACTION: '/dev/extraction',
  ENTRY_AUDIT: '/entry-audit',
} as const;

// brand / static assets (served from /public in Vite)
export const ASSETS = {
  LOGO_MARK: '/logo-mark.png',
  FAVICON: '/favicon.png',
} as const;

// App navigation lives in the URL fragment: the app is served as static files,
// so the hash never reaches the server and needs no SPA-fallback config. This is
// the SSOT for the URL <-> app-location map — the view names, the reader path,
// and the parse/serialize pair. Nothing else reads or formats the hash.
// 'design' is the living styleguide: a valid route (#/design) intentionally
// kept out of the nav bar (NAV in app/shell/nav.ts is the visible subset).
// 'extraction' is the extraction inspector and IS a visible nav item; it needs
// the backend's SOL_DEV_TOOLS opt-in, and without it the /api/dev routes 404
// and the screen shows that state.
const NAV_VIEWS = ['home', 'library', 'quran', 'graph', 'design', 'extraction'] as const;
export type NavView = (typeof NAV_VIEWS)[number];

const DEFAULT_VIEW: NavView = 'home';
const READ_SEGMENT = 'read';

export interface RouteState {
  view: NavView;
  query: string;
  scope: string;
  /** Library deep-link: open scoped to this category slug ('' = none). */
  cat: string;
  /** Library deep-link: open scoped to this domain id ('' = none). */
  dom: string;
  /** `query` here is the highlight term the reader opened for (e.g. the
      search hit that led here), never the header search box — that's the
      top-level `query` above. '' when the reader was opened with no term. */
  reading: { urn: string; page: number; query: string } | null;
  /** Content-scope search filters — match mode, the multi-select category
      slugs, and the active-book drill-in — round-tripped through the URL so
      a search's exact filters survive a bookmark, a reload, or a trip
      through the Reader and back. Only meaningful, and only serialized,
      when scope === 'content'. */
  mode: string;
  categories: string[];
  book: string;
  /** Qurʾān deep-link: the verse to open focused (e.g. from a citation link in
      the reader). Only meaningful, and only serialized, when view === 'quran'. */
  focus: { surah: number; aya: number } | null;
}

function isNavView(value: string): value is NavView {
  return (NAV_VIEWS as readonly string[]).includes(value);
}

/** Every RouteState field but `view`, at its empty/default value. The one
    base a caller building a one-off link (a bare view, a library deep-link)
    spreads over, instead of re-listing all eight fields at each call site. */
export const EMPTY_ROUTE: Omit<RouteState, 'view'> = {
  query: '',
  scope: '',
  cat: '',
  dom: '',
  reading: null,
  mode: SEARCH.DEFAULT_MODE,
  categories: [],
  book: '',
  focus: null,
};

/** The reader's path segment (no query string): shared by readingHref below
    and parseHash's reading-branch match, so the segment format lives once. */
function readingSegment(urn: string, page: number): string {
  return `/${READ_SEGMENT}/${encodeURIComponent(urn)}/${page}`;
}

/** The one place a reader URL is composed, path plus its optional highlight
    query — used by buildHash's reading branch AND the standalone readerHref,
    so an in-place "open in a new tab" link, a real page load, and the app's
    own navigation can never disagree about what the highlight term was.
    Base64url-encoded (toBase64Url): percent-encoding a diacritic-heavy
    Arabic phrase roughly triples its length, which is exactly the free text
    this param carries. */
function readingHref(urn: string, page: number, query: string): string {
  const params = new URLSearchParams();
  const q = query.trim();
  if (q) params.set('q', toBase64Url(q));
  const qs = params.toString();
  return `#${readingSegment(urn, page)}${qs ? `?${qs}` : ''}`;
}

/** Serialize app location to a hash fragment. The reader is a path; an active
    header search is a query string layered on the current view. */
export function buildHash(state: RouteState): string {
  if (state.reading) {
    return readingHref(state.reading.urn, state.reading.page, state.reading.query);
  }
  const path = state.view === DEFAULT_VIEW ? '/' : `/${state.view}`;
  const params = new URLSearchParams();
  const q = state.query.trim();
  if (q) {
    params.set('q', toBase64Url(q));
    if (state.scope) params.set('scope', state.scope);
    if (state.scope === 'content') {
      if (state.mode && state.mode !== SEARCH.DEFAULT_MODE) params.set('mode', state.mode);
      for (const category of state.categories) params.append('category', category);
      if (state.book) params.set('book', toBase64Url(state.book));
    }
  }
  if (state.view === 'library') {
    if (state.cat) params.set('cat', state.cat);
    else if (state.dom) params.set('dom', state.dom);
  }
  if (state.view === 'quran' && state.focus) {
    params.set('s', String(state.focus.surah));
    params.set('a', String(state.focus.aya));
  }
  const qs = params.toString();
  return `#${path}${qs ? `?${qs}` : ''}`;
}

/** The canonical href for a top-level view. Static `<a href>`s go through the
    same serializer as navigation, so a middle-click or copy-link round-trips
    through parseHash instead of relying on parser mercy (#/ , not #home). */
export function viewHref(view: NavView): string {
  return buildHash({ view, ...EMPTY_ROUTE });
}

/** The canonical href for a Qurʾān verse: a search result row's "open in a new
    tab" and its in-place click both resolve through this, so either one lands
    in the reader on that exact āya, with the rest of its sūra around it. */
export function quranVerseHref(surah: number, aya: number): string {
  return buildHash({ view: 'quran', ...EMPTY_ROUTE, focus: { surah, aya } });
}

/** The canonical href for a reader position, e.g. a search result row: the
    optional `query` is the term to highlight/search for once the reader
    opens, so a new tab or a bookmark lands exactly where an in-place click
    would have. */
export function readerHref(urn: string, page: number, query = ''): string {
  return readingHref(urn, page, query);
}

/** Parse a hash fragment back to app location. Unknown shapes fall back to the
    default view; this never throws. */
export function parseHash(hash: string): RouteState {
  const raw = hash.replace(/^#/, '');
  const [path, queryString] = raw.split('?');
  const segments = path.split('/').filter(Boolean);
  const params = new URLSearchParams(queryString ?? '');

  if (segments[0] === READ_SEGMENT && segments[1]) {
    const page = Number(segments[2]);
    return {
      ...EMPTY_ROUTE,
      view: DEFAULT_VIEW,
      reading: {
        urn: decodeURIComponent(segments[1]),
        page: Number.isFinite(page) && page > 0 ? page : 1,
        query: fromBase64Url(params.get('q') ?? ''),
      },
    };
  }
  const surah = Number(params.get('s'));
  const aya = Number(params.get('a'));
  const view = segments[0] ?? DEFAULT_VIEW;
  const resolved = isNavView(view) ? view : DEFAULT_VIEW;
  return {
    view: resolved,
    query: fromBase64Url(params.get('q') ?? ''),
    scope: params.get('scope') ?? '',
    cat: resolved === 'library' ? (params.get('cat') ?? '') : '',
    dom: resolved === 'library' ? (params.get('dom') ?? '') : '',
    reading: null,
    mode: params.get('mode') ?? SEARCH.DEFAULT_MODE,
    categories: params.getAll('category'),
    book: fromBase64Url(params.get('book') ?? ''),
    focus: resolved === 'quran' && surah >= 1 && aya >= 1 ? { surah, aya } : null,
  };
}
