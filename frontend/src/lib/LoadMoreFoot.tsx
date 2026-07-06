import type { ReactNode } from 'react';
import { Button, Spinner, Text } from './design-system';
import './LoadMoreFoot.css';

export interface LoadMoreFootProps {
  /** The honesty line: always states how much of what is on screen,
      e.g. "Showing 100 of 1,204 works". Callers compose it with countLabel. */
  line: ReactNode;
  /** True while the next page is loading; shows the spinner in place of the
      button. Omit for client-side windowing, which has no loading state. */
  loading?: boolean;
  spinnerLabel?: string;
  /** True when more rows exist beyond the window. */
  hasMore: boolean;
  onMore: () => void;
  moreLabel?: string;
  /** 'secondary' (default), or 'link' where a button would outweigh the
      surface (the Qurʾān finder's rail). */
  moreVariant?: 'secondary' | 'link';
}

/** The one foot under a paged or windowed list: the count line on the left,
    the load-more control on the right. Every list that can show less than it
    matched closes with this, so the footer grammar and its spacing cannot
    drift per feature. */
export function LoadMoreFoot({
  line,
  loading = false,
  spinnerLabel = 'Loading more',
  hasMore,
  onMore,
  moreLabel = 'Show more',
  moreVariant = 'secondary',
}: LoadMoreFootProps) {
  return (
    <footer className="loadfoot">
      <Text size="xs" tone="faint" font="mono">
        {line}
      </Text>
      {loading ? <Spinner label={spinnerLabel} /> : null}
      {!loading && hasMore ? (
        moreVariant === 'link' ? (
          <Button variant="link" onClick={onMore}>
            {moreLabel}
          </Button>
        ) : (
          <Button variant="secondary" size="sm" onClick={onMore}>
            {moreLabel}
          </Button>
        )
      ) : null}
    </footer>
  );
}
