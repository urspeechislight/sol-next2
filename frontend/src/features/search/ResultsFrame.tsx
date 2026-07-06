import type { ReactNode } from 'react';

import { Spinner, Stack } from '../../lib/design-system';
import { EmptyText, ErrorText } from '../../lib/DataView';
import { SearchFilters } from './SearchFilters';
import type { SearchFiltersProps } from './SearchFilters';
import './SearchResults.css';

export interface ResultsFrameProps {
  /** The one filter bar: the result count always, plus whatever controls the
      scope supports (match mode for corpus, a category filter where there are
      facets). Every search scope renders through this frame, so the bar, the
      promoted count, and the result rows read identically across scopes. */
  filters: SearchFiltersProps;
  /** The scope's orientation layer between the bar and the rows, e.g. the
      content scope's distribution map (or its honest cap notice). */
  map?: ReactNode;
  loading: boolean;
  loadingLabel: string;
  error?: string | null;
  /** Message shown when the search resolved with no results. */
  empty?: string | null;
  /** The result rows. Scopes own their row markup and its container. */
  children?: ReactNode;
  /** The honest foot under the rows (showing X of Y + load-more). */
  foot?: ReactNode;
}

/** Layout SSOT for a scope's results: filter bar + map + loading/error/empty
    + rows + the honest foot. Scopes own their fetching and their row shape;
    the framing lives here. */
export function ResultsFrame({
  filters,
  map,
  loading,
  loadingLabel,
  error,
  empty,
  children,
  foot,
}: ResultsFrameProps) {
  return (
    <Stack gap="md">
      <SearchFilters {...filters} />
      {map}
      {loading ? <Spinner label={loadingLabel} /> : null}
      {error ? <ErrorText>{error}</ErrorText> : null}
      {empty ? <EmptyText>{empty}</EmptyText> : null}
      {children}
      {foot}
    </Stack>
  );
}
