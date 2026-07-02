// constants.ts:non-design, non-path literals. SCREAMING_SNAKE_CASE, grouped.
// Path / URL constants (API, ROUTES, ASSETS) live in routes.ts (CENTRAL-006).

export const PAGE = {
  defaultLimit: 24,
  // Book / narrator scopes facet (category filter) over the returned rows on the
  // client, so they fetch a deeper page than the default to keep that facet and
  // its counts complete for realistic result sets.
  facetLimit: 200,
  graphPerPage: 40,
} as const;

// Sentinel the upstream catalog uses for an unknown author death year; the
// library treats it as "no year" rather than printing it.
export const BOOK = { UNKNOWN_DEATH_YEAR: 99999 } as const;

// The library's category browse loads the whole scope (paged fetches of
// PAGE.facetLimit) so it can shelve landmarks and group by era client-side;
// categoryMax bounds the assembly and the pane says so when a scope exceeds it;
// volumeViewMax caps the flat by-volumes ordering (the grouped views cover all).
export const LIBRARY = { categoryMax: 600, volumeViewMax: 60 } as const;

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
  CANONICAL: 'canonical',
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
