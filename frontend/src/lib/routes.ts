// routes.ts:SSOT for path / URL constants: API endpoints, app routes, asset
// URLs. CENTRAL-006 requires frontend path literals to live here, never inline
// in components. (Split out of the design source's constants.ts.)

export const API = {
  BASE: '/api',
  RIJAL: '/rijal',
  CANONICAL: '/canonical',
  HISTORY: '/history',
  BOOKS: '/books',
  DATA: '/data',
  PAGE: '/page',
  SHARE: '/share',
} as const;

export const ROUTES = {
  HOME: '/',
  READER: '/reader',
  BOOK: '/reader/book',
  GRAPH_RIJAL: '/graph/rijal',
  GRAPH_CANONICAL: '/graph/canonical',
  GRAPH_HISTORY: '/graph/history',
} as const;

// brand / static assets (served from /public in Vite)
export const ASSETS = {
  LOGO_MARK: '/logo-mark.png',
  FAVICON: '/favicon.png',
} as const;
