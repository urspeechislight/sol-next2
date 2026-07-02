// routes.ts:SSOT for path / URL constants: API endpoints, app routes, asset
// URLs. CENTRAL-006 requires frontend path literals to live here, never inline
// in components, the client, or the vite proxy config.

export const API = {
  BASE: '/api',
  RIJAL: '/rijal',
  CANONICAL: '/canonical',
  BOOKS: '/books',
  WORKS: '/works',
  DOMAINS: '/domains',
  DAILY: '/daily',
  ALMANAC: '/almanac',
  TOC: '/toc',
  PAGES: '/pages',
  VOLUMES: '/volumes',
  SEARCH: '/search',
  FACETS: '/facets',
  QURAN: '/quran',
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
// 'design' is the living styleguide: a valid route (#/design) but intentionally
// not in the nav bar (NAV in app/shell/nav.ts is the visible subset).
const NAV_VIEWS = ['home', 'library', 'quran', 'graph', 'design'] as const;
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
  reading: { urn: string; page: number } | null;
}

function isNavView(value: string): value is NavView {
  return (NAV_VIEWS as readonly string[]).includes(value);
}

/** Serialize app location to a hash fragment. The reader is a path; an active
    header search is a query string layered on the current view. */
export function buildHash(state: RouteState): string {
  if (state.reading) {
    return `#/${READ_SEGMENT}/${encodeURIComponent(state.reading.urn)}/${state.reading.page}`;
  }
  const path = state.view === DEFAULT_VIEW ? '/' : `/${state.view}`;
  const params = new URLSearchParams();
  const q = state.query.trim();
  if (q) {
    params.set('q', q);
    if (state.scope) params.set('scope', state.scope);
  }
  if (state.view === 'library') {
    if (state.cat) params.set('cat', state.cat);
    else if (state.dom) params.set('dom', state.dom);
  }
  const qs = params.toString();
  return `#${path}${qs ? `?${qs}` : ''}`;
}

/** The canonical href for a top-level view. Static `<a href>`s go through the
    same serializer as navigation, so a middle-click or copy-link round-trips
    through parseHash instead of relying on parser mercy (#/ , not #home). */
export function viewHref(view: NavView): string {
  return buildHash({ view, query: '', scope: '', cat: '', dom: '', reading: null });
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
      view: DEFAULT_VIEW,
      query: '',
      scope: '',
      cat: '',
      dom: '',
      reading: {
        urn: decodeURIComponent(segments[1]),
        page: Number.isFinite(page) && page > 0 ? page : 1,
      },
    };
  }
  const view = segments[0] ?? DEFAULT_VIEW;
  const resolved = isNavView(view) ? view : DEFAULT_VIEW;
  return {
    view: resolved,
    query: params.get('q') ?? '',
    scope: params.get('scope') ?? '',
    cat: resolved === 'library' ? (params.get('cat') ?? '') : '',
    dom: resolved === 'library' ? (params.get('dom') ?? '') : '',
    reading: null,
  };
}
