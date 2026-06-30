import type { ReactNode } from 'react';
import { Spinner, Text } from './design-system';

/** The shape useAsync returns (data | error | loading), accepted structurally so
    a screen holding the pieces as separate props can pass `{ data, error, loading }`. */
export interface AsyncLike<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

export interface DataViewProps<T> {
  result: AsyncLike<T>;
  loadingLabel?: string;
  /** Custom loading node, overriding the default bare Spinner (e.g. a centered wrapper). */
  renderLoading?: () => ReactNode;
  /** Prefix for the default danger message ("<errorText>: <message>"). */
  errorText?: string;
  /** Custom error node, overriding the default danger Text (e.g. a bespoke card). */
  renderError?: (error: Error) => ReactNode;
  /** Predicate marking loaded-but-empty data; renders the empty slot. */
  isEmpty?: (data: T) => boolean;
  /** Message for the default muted empty state. */
  emptyText?: string;
  /** Custom empty node, overriding the default muted Text. */
  renderEmpty?: () => ReactNode;
  /** Renders the loaded, non-empty data. Receives a guaranteed-non-null value. */
  children: (data: T) => ReactNode;
}

/** The one loading/error/empty/data ladder. Replaces the hand-rolled
    `{loading?<Spinner/>}{error?<Text/>}{empty?…}{data?…}` chain repeated across
    screens, while keeping each slot overridable: a screen with a bespoke error or
    empty card passes renderError/renderEmpty instead of the default texts. */
export function DataView<T>({
  result,
  loadingLabel = 'Loading',
  renderLoading,
  errorText,
  renderError,
  isEmpty,
  emptyText,
  renderEmpty,
  children,
}: DataViewProps<T>) {
  if (result.loading) {
    if (renderLoading) return <>{renderLoading()}</>;
    return <Spinner label={loadingLabel} />;
  }
  if (result.error) {
    if (renderError) return <>{renderError(result.error)}</>;
    return (
      <Text as="p" size="sm" tone="danger">
        {errorText ?? 'Could not load this'}: {result.error.message}
      </Text>
    );
  }
  if (result.data === null) return null;
  if (isEmpty?.(result.data)) {
    if (renderEmpty) return <>{renderEmpty()}</>;
    return (
      <Text as="p" size="sm" tone="muted">
        {emptyText ?? 'Nothing here yet.'}
      </Text>
    );
  }
  return <>{children(result.data)}</>;
}
