import { useSyncExternalStore } from 'react';

import { THEME } from './constants';

// useTheme.ts: the one source of truth for the app theme. The html attribute
// is what CSS reads, localStorage is what index.html's pre-paint script reads
// (so a dark visitor never sees a light flash), and this store is what React
// reads. The reader surfaces derive from it: a surface with its own picker
// (the book reader) overrides; a surface without one (the Qurʾan page) takes
// the derived value.

const listeners = new Set<() => void>();

function isDark(): boolean {
  return document.documentElement.getAttribute(THEME.ATTR) === THEME.DARK;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function setDark(dark: boolean): void {
  document.documentElement.setAttribute(THEME.ATTR, dark ? THEME.DARK : THEME.LIGHT);
  localStorage.setItem(THEME.STORAGE_KEY, dark ? THEME.DARK : THEME.LIGHT);
  for (const notify of listeners) notify();
}

/** The reactive app theme: `dark` re-renders every consumer when any of them
    toggles. */
export function useTheme(): { dark: boolean; toggle: () => void } {
  const dark = useSyncExternalStore(subscribe, isDark);
  return { dark, toggle: () => setDark(!dark) };
}
