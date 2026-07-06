import { Spinner } from '../../lib/design-system';
import { DataView } from '../../lib/DataView';
import type { Work } from '../../lib/types';
import { countLabel } from '../../lib/utils';
import { FacetedWorksList } from './FacetedWorksList';
import { FoundationalShelf } from './FoundationalShelf';
import { ScopeHead } from './ScopeHead';

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
  return (
    <DataView
      result={{ data: works, error, loading }}
      renderLoading={() => (
        <div className="library__loading">
          <Spinner label="Loading the category" />
        </div>
      )}
      errorText="Could not load works"
    >
      {(data) => (
        <section className="works cpane">
          <ScopeHead
            breadcrumb={breadcrumb}
            labelAr={scopeLabelAr}
            line={`${scopeLabel} · ${countLabel(total, 'work')}`}
          />
          <FoundationalShelf category={category} onOpen={onOpen} />
          <FacetedWorksList works={data} total={total} onOpen={onOpen} />
        </section>
      )}
    </DataView>
  );
}
