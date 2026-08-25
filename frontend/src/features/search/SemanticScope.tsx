import { Icon, Text } from '../../lib/design-system';
import { searchFacetsSemantic, searchSemantic } from '../../lib/api/client';
import { SCOPE_OPTIONS } from '../../lib/scopes';
import { CorpusResults } from './CorpusResults';
import type { CorpusFetcher } from './CorpusResults';
import './SearchResults.css';

/** The LLM scope: the same CorpusResults engine as the content scope, bound
    to the semantic endpoints. The backend plans the question into Arabic
    phrases + corpus scopes (categories and named works) and executes them on
    the one corpus engine, so the distribution map, taxonomy filters, works
    FilterBar, and book drill-in all work exactly as in keyword search. */
const semanticFetcher: CorpusFetcher = {
  matches: (q, scope) => searchSemantic(q, scope),
  facets: (q, _mode, categories) => searchFacetsSemantic(q, categories),
};

export interface SemanticScopeProps {
  q: string;
  onOpenReader: (urn: string, page: number, query: string) => void;
}

export function SemanticScope({ q, onOpenReader }: SemanticScopeProps) {
  const option = SCOPE_OPTIONS.find((o) => o.value === 'semantic');
  return (
    <>
      {option ? (
        <Text as="p" size="sm" tone="muted">
          <Icon name={option.icon} size="sm" /> {option.label} search — your question is planned
          into Arabic phrases and corpus scopes, then answered by the same index as a keyword
          search.
        </Text>
      ) : null}
      <CorpusResults
        q={q}
        onOpenReader={onOpenReader}
        fetcher={semanticFetcher}
        lockMode
        loadingLabel="Planning and searching"
      />
    </>
  );
}
