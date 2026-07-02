import { useCallback, useEffect, useRef, useState } from 'react';

import type { Page } from './types';

export interface PagedResult<T> {
  /** Every row fetched so far, in server order. */
  items: T[];
  /** The server's total for the query, or null before the first response. */
  total: number | null;
  loading: boolean;
  error: Error | null;
  /** True while the server holds more rows than are loaded. */
  hasMore: boolean;
  /** Fetch the next page and append it. */
  more: () => void;
}

/** Accumulating pagination over a paged endpoint: deps reset the list and
    fetch the first page, ``more`` appends the next. Responses landing after
    the deps changed are dropped (each fetch run is keyed to its epoch), so a
    stale page can never mix into a newer query's rows. Errors surface; they
    are never swallowed into an empty page. */
export function usePaged<T>(
  fetchPage: (offset: number) => Promise<Page<T>>,
  deps: readonly unknown[],
): PagedResult<T> {
  const [items, setItems] = useState<T[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const epoch = useRef(0);

  const load = useCallback(
    (offset: number) => {
      const run = epoch.current;
      setLoading(true);
      setError(null);
      fetchPage(offset)
        .then((page) => {
          if (epoch.current !== run) return;
          setItems((prev) => (offset === 0 ? page.items : [...prev, ...page.items]));
          setTotal(page.total);
          setLoading(false);
        })
        .catch((err: unknown) => {
          if (epoch.current !== run) return;
          setError(err instanceof Error ? err : new Error(String(err)));
          setLoading(false);
        });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    deps,
  );

  useEffect(() => {
    epoch.current += 1;
    setItems([]);
    setTotal(null);
    load(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  const more = useCallback(() => load(items.length), [load, items.length]);
  const hasMore = total !== null && items.length < total;
  return { items, total, loading, error, hasMore, more };
}
