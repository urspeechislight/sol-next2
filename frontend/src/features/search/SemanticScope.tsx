import { useMemo, useState } from 'react';

import { Icon, Text } from '../../lib/design-system';
import { searchSemantic } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import { SCOPE_OPTIONS } from '../../lib/scopes';
import { usePaged } from '../../lib/usePaged';
import type { CorpusMatch } from '../../lib/types';
import { countLabel, formatCount } from '../../lib/utils';
import { LoadMoreFoot } from '../../lib/LoadMoreFoot';
import { PassageGroups } from './PassageGroups';
import { ResultsFrame } from './ResultsFrame';

export interface SemanticScopeProps {
  q: string;
  onOpenReader: (urn: string, page: number, query: string) => void;
}

/** The LLM scope: a freeform (usually English) question is planned by the
    backend's LLM into category scopes + Arabic phrases and executed by the
    corpus engine, so the rows are ordinary passage hits in the shared
    anthology grammar — no planner output is ever rendered. The work-head
    drill-in narrows the loaded window client-side (the planner already chose
    the scope, so there are no taxonomy filters to expose). */
export function SemanticScope({ q, onOpenReader }: SemanticScopeProps) {
  const corpus = usePaged<CorpusMatch>(
    (offset) => searchSemantic(q, { limit: PAGE.defaultLimit, offset }),
    [q],
  );
  const [activeBook, setActiveBook] = useState('');
  const option = SCOPE_OPTIONS.find((o) => o.value === 'semantic');
  const total = corpus.total ?? 0;
  const firstLoad = corpus.loading && corpus.items.length === 0;
  const items = useMemo(
    () => (activeBook ? corpus.items.filter((m) => m.title_ar === activeBook) : corpus.items),
    [corpus.items, activeBook],
  );
  return (
    <>
      {option ? (
        <Text as="p" size="sm" tone="muted">
          <Icon name={option.icon} size="sm" /> {option.label} search — your question is planned
          into Arabic phrases and corpus scopes, then answered by the same index as a keyword
          search.
        </Text>
      ) : null}
      <ResultsFrame
        filters={{ total }}
        loading={firstLoad}
        loadingLabel="Planning and searching"
        error={corpus.error ? `LLM search is unavailable: ${corpus.error.message}` : null}
        empty={
          !corpus.loading && corpus.total !== null && corpus.items.length === 0
            ? `No passages match “${q}”.`
            : null
        }
        foot={
          corpus.items.length > 0 ? (
            <LoadMoreFoot
              line={`Showing ${formatCount(corpus.items.length)} of ${countLabel(total, 'passage')}`}
              loading={corpus.loading}
              spinnerLabel="Loading more passages"
              hasMore={corpus.hasMore}
              onMore={corpus.more}
            />
          ) : null
        }
      >
        {items.length > 0 ? (
          <PassageGroups
            items={items}
            q={q}
            activeBook={activeBook}
            bookCounts={new Map()}
            filteredWorks={null}
            onPickBook={setActiveBook}
            onOpen={(urn, page) => onOpenReader(urn, page, q)}
          />
        ) : null}
      </ResultsFrame>
    </>
  );
}
