import type { ReactNode } from 'react';

import { Spinner, Stack, Text } from '../../lib/design-system';
import { SearchFilters } from './SearchFilters';
import type { SearchFiltersProps } from './SearchFilters';
import './SearchResults.css';

export interface ResultsFrameProps {
  /** The one filter bar: the result count always, plus whatever controls the
      scope supports (match mode for corpus, a category filter where there are
      facets). Every search scope renders through this frame, so the bar, the
      promoted count, and the record list read identically across scopes. */
  filters: SearchFiltersProps;
  loading: boolean;
  loadingLabel: string;
  error?: string | null;
  /** Message shown when the search resolved with no results. */
  empty?: string | null;
  /** The record rows (already mapped to SourceRecord / NarratorCard / etc.). */
  children?: ReactNode;
}

/** Layout SSOT for a scope's results: filter bar + loading/error/empty + rows.
    Scopes own their fetching and their record shape; the framing lives here. */
export function ResultsFrame({
  filters,
  loading,
  loadingLabel,
  error,
  empty,
  children,
}: ResultsFrameProps) {
  return (
    <Stack gap="md">
      <SearchFilters {...filters} />
      {loading ? <Spinner label={loadingLabel} /> : null}
      {error ? (
        <Text as="p" size="sm" tone="muted">
          {error}
        </Text>
      ) : null}
      {empty ? (
        <Text as="p" size="sm" tone="muted">
          {empty}
        </Text>
      ) : null}
      {children ? <div className="ds-records">{children}</div> : null}
    </Stack>
  );
}
