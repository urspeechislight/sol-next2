import { useEffect, useRef } from 'react';
import { buildHash, parseHash } from './routes';
import type { RouteState } from './routes';

/** The single URL <-> state bridge. Writes app location into the hash (pushing
    history so Back/Forward and copy-paste both work) and reports user-driven
    hash changes (Back/Forward, manual edits) via onPop. The hash is the only
    place app navigation is read from or written to. */
export function useHashRoute(state: RouteState, onPop: (next: RouteState) => void): void {
  const hash = buildHash(state);
  const mounted = useRef(false);

  useEffect(() => {
    if (hash !== window.location.hash) {
      if (mounted.current) window.history.pushState(null, '', hash);
      else window.history.replaceState(null, '', hash);
    }
    mounted.current = true;
  }, [hash]);

  useEffect(() => {
    const sync = () => onPop(parseHash(window.location.hash));
    window.addEventListener('hashchange', sync);
    window.addEventListener('popstate', sync);
    return () => {
      window.removeEventListener('hashchange', sync);
      window.removeEventListener('popstate', sync);
    };
  }, [onPop]);
}
