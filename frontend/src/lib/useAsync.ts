// useAsync.ts:tiny data-fetching hook shared by the screens. It calls a client
// function (never fetch directly — CENTRAL-007 keeps fetch in api/) and exposes
// {data,error,loading}, cancelling stale results when deps change or unmount.
import { useEffect, useState } from 'react';

export interface AsyncState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

const promiseCache = new Map<string, Promise<unknown>>();

/** useAsync over a module-lifetime promise cache, for immutable corpus data
    (the taxonomy, the narrator index) that several screens request. The first
    caller starts the fetch; everyone since (including concurrent mounts)
    shares the same promise. A rejected promise is evicted so the next mount
    retries instead of caching the failure. */
export function useCachedAsync<T>(key: string, run: () => Promise<T>): AsyncState<T> {
  return useAsync<T>(() => {
    const hit = promiseCache.get(key);
    if (hit) return hit as Promise<T>;
    const started = run().catch((cause: unknown) => {
      promiseCache.delete(key);
      throw cause;
    });
    promiseCache.set(key, started);
    return started;
  }, [key]);
}

export function useAsync<T>(run: () => Promise<T>, deps: readonly unknown[]): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ data: null, error: null, loading: true });

  useEffect(() => {
    let live = true;
    setState({ data: null, error: null, loading: true });
    run().then(
      (data) => {
        if (live) setState({ data, error: null, loading: false });
      },
      (cause: unknown) => {
        const error = cause instanceof Error ? cause : new Error(String(cause));
        if (live) setState({ data: null, error, loading: false });
      },
    );
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
