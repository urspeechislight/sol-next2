// constants.ts — non-design, non-path literals. SCREAMING_SNAKE_CASE, grouped.
// Path / URL constants (API, ROUTES, ASSETS) live in routes.ts (CENTRAL-006).

export const PAGE = {
  defaultPage: 1,
  defaultPerPage: 24,
} as const;

// the three graph registries — drives nav + screen config
export const REGISTRY = {
  RIJAL: "rijal",
  CANONICAL: "canonical",
  HISTORY: "history",
} as const;

export type RegistryKey = (typeof REGISTRY)[keyof typeof REGISTRY];

export const BREAKPOINTS = { SM: 640, MD: 880, LG: 1080, XL: 1320 } as const;

// Motion durations in ms for JS-driven timing. MUST mirror tokens.css
// --dur-raw-fast/base/slow (the motion SSOT); keep the two in lockstep.
export const DURATION_MS = { FAST: 120, BASE: 200, SLOW: 340 } as const;

export const THEME = {
  ATTR: "data-theme",
  LIGHT: "light",
  DARK: "dark",
  STORAGE_KEY: "sol-theme",
} as const;

export const DENSITY = {
  ATTR: "data-density",
  COMFORTABLE: "comfortable",
  COMPACT: "compact",
} as const;

// reader surface controls. SIZE_DEFAULT mirrors tokens.css --reader-size (19px);
// keep them equal across the JS/CSS boundary.
export const READER = {
  THEME_ATTR: "data-reader-theme",
  LANG_ATTR: "data-lang",
  SIZE_MIN: 15,
  SIZE_MAX: 28,
  SIZE_STEP: 1,
  SIZE_DEFAULT: 19,
} as const;

export const READER_THEMES = [
  { value: "bright", label: "Bright" },
  { value: "dark", label: "Dark" },
  { value: "classical", label: "Classical" },
] as const;

// reader shows AR / EN / both — English-primary ordering
export const LANG_MODES = [
  { value: "en", label: "EN" },
  { value: "both", label: "EN | AR" },
  { value: "ar", label: "AR" },
] as const;
