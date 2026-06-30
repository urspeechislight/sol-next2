// useAsync.ts:tiny data-fetching hook shared by the screens. It calls a client
// function (never fetch directly — CENTRAL-007 keeps fetch in api/) and exposes
// {data,error,loading}, cancelling stale results when deps change or unmount.
import { useEffect, useState } from 'react';

export interface AsyncState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
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
