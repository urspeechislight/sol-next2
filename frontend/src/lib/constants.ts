// constants.ts:non-design, non-path literals. SCREAMING_SNAKE_CASE, grouped.
// Path / URL constants (API, ROUTES, ASSETS) live in routes.ts (CENTRAL-006).

import type { SearchMode } from './types';

export const PAGE = {
  defaultLimit: 24,
  // Book / narrator scopes facet (category filter) over the returned rows on the
  // client, so they fetch a deeper page than the default to keep that facet and
  // its counts complete for realistic result sets.
  facetLimit: 200,
  graphPerPage: 40,
} as const;

// The library's category browse loads the whole scope (paged fetches of
// PAGE.facetLimit) and filters client-side; listPageSize is the load-more
// window of the honest list (never a cap: the foot always states the total).
// The domain pane's schools spread previews each category with sectionSpread
// rows after edition-dedupe, fetching sectionFetch of margin so duplicate
// editions cannot starve a preview; the section head always states the true
// category totals, so the preview never reads as the whole.
// assembleMax bounds full client-side assembly of a works-search scope: true
// facet counts need the whole scope in hand, which measures ~1s at 941 works
// and is infeasible at the 8,872 a degenerate query matches. At or below the
// bound the list assembles and facets; above it the surface switches to a
// STATED canonical-ranked paged mode (never a silent cap).
export const LIBRARY = {
  listPageSize: 100,
  sectionSpread: 3,
  sectionFetch: 12,
  assembleMax: 1000,
} as const;

// Landing-page motion: the verse reveals one word per tick, rests for the hold
// ticks, then loops; tafsīr excerpts rotate on their own slower clock.
export const HOME = {
  VERSE_WORD_MS: 420,
  VERSE_HOLD_TICKS: 8,
  TAFSIR_ROTATE_MS: 8000,
} as const;

// the narrator registries that the graph browses
export const REGISTRY = {
  RIJAL: 'rijal',
  PERSON: 'person',
} as const;

export const THEME = {
  ATTR: 'data-theme',
  LIGHT: 'light',
  DARK: 'dark',
  STORAGE_KEY: 'sol-theme',
} as const;

// reader surface controls. SIZE_DEFAULT mirrors tokens.css --reader-size (19px);
// keep them equal across the JS/CSS boundary.
export const READER = {
  THEME_ATTR: 'data-reader-theme',
  LANG_ATTR: 'data-lang',
  SIZE_MIN: 15,
  SIZE_MAX: 28,
  SIZE_STEP: 1,
  SIZE_DEFAULT: 19,
} as const;

// Continuity without accounts: the reader's last position (written by App as
// the reader turns pages, read by the landing page's resume strip).
export const READING = { STORAGE_KEY: 'sol-reading' } as const;

// Search history: the header remembers past searches the same way (no
// accounts, so continuity lives in localStorage); capped so the dropdown
// stays a short recency list, not an unbounded log.
export const SEARCH_HISTORY = { STORAGE_KEY: 'sol-search-history', MAX_ENTRIES: 8 } as const;

// The content scope's default match mode: what an unqualified search means.
// Typed against the served SearchMode so a backend rename fails the build
// here instead of silently minting an unknown mode. Consumed by routes.ts
// (hash serialization), api/client.ts (request defaults), and ContentScope.
export const SEARCH = { DEFAULT_MODE: 'exact' } as const satisfies { DEFAULT_MODE: SearchMode };

// Share card formats + platform targets (consumed by ShareSheet).
export const SHARE_FORMATS = [
  { value: 'square', label: 'Square' },
  { value: 'story', label: 'Story' },
  { value: 'link', label: 'Link' },
] as const;
// Derived from the const above (not hand-listed), so the type can never drift
// from the runtime options, mirroring how SearchScope derives from SEARCH_SCOPES.
export type ShareFormat = (typeof SHARE_FORMATS)[number]['value'];

export const SHARE_PLATFORMS = [
  { id: 'x', label: 'X', icon: 'x' },
  { id: 'facebook', label: 'Facebook', icon: 'facebook' },
  { id: 'instagram', label: 'Instagram', icon: 'instagram' },
  { id: 'tiktok', label: 'TikTok', icon: 'tiktok' },
] as const;
