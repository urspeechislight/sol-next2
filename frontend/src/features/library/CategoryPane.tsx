import { Spinner, Text } from '../../lib/design-system';
import type { Work } from '../../lib/types';
import { FacetedWorksList } from './FacetedWorksList';
import { FoundationalShelf } from './FoundationalShelf';
import { ScopeHead } from './ScopeHead';
import { countLabel } from './lib';

export interface CategoryPaneProps {
  breadcrumb: string;
  scopeLabel: string;
  scopeLabelAr: string;
  category: string;
  works: Work[] | null;
  total: number;
  loading: boolean;
  error: Error | null;
  onOpen: (urn: string, page?: number) => void;
}

/** A category as one honest list under combinable facets: the foundational
    shelf (when the category has primary references), then the shared
    FacetedWorksList in its era-sectioned browsing default. Load-more paging
    keeps the count truthful; nothing is capped or hidden. */
export function CategoryPane({
  breadcrumb,
  scopeLabel,
  scopeLabelAr,
  category,
  works,
  total,
  loading,
  error,
  onOpen,
}: CategoryPaneProps) {
  if (loading) {
    return (
      <div className="library__loading">
        <Spinner label="Loading the category" />
      </div>
    );
  }
  if (error || !works) {
    return (
      <Text as="p" size="sm" tone="danger">
        Could not load works{error ? `: ${error.message}` : ''}.
      </Text>
    );
  }

  return (
    <section className="works cpane">
      <ScopeHead
        breadcrumb={breadcrumb}
        labelAr={scopeLabelAr}
        line={`${scopeLabel} · ${countLabel(total, 'work')}`}
      />
      <FoundationalShelf category={category} onOpen={onOpen} />
      <FacetedWorksList works={works} total={total} onOpen={onOpen} />
    </section>
  );
}
