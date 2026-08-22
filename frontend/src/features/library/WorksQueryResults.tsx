import { Apparatus, Text } from '../../lib/design-system';
import { DataView, ErrorText } from '../../lib/DataView';
import { LoadMoreFoot } from '../../lib/LoadMoreFoot';
import { getWorks } from '../../lib/api/client';
import { LIBRARY, PAGE } from '../../lib/constants';
import type { Work } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { usePaged } from '../../lib/usePaged';
import { countLabel, formatCount } from '../../lib/utils';
import { FacetedWorksList } from './FacetedWorksList';
import { assembleWorks } from './lib';
import { WorkRecord } from './WorkRecord';

export interface WorksQueryResultsProps {
  q: string;
  /** Tradition lens filter; '' keeps every tradition. */
  tradition?: string;
  onOpen: (urn: string, page?: number) => void;
}

interface Probe {
  /** The fully assembled scope, or null when the total exceeds assembleMax. */
  works: Work[] | null;
  total: number;
}

/** One works-search result surface for every entry point (header Works scope,
    library rail search): volume-folded matches in canonical-rank order, so the
    most famous match is row one. Under LIBRARY.assembleMax matches the whole
    scope is assembled and rendered through the shared FacetedWorksList (true
    era counts, author filter, foundational toggle). Above it, faceting would
    need counts nobody has fetched, so the surface switches to a STATED
    ranked-pages mode: server-paged canonical order, load-more, the honest
    foot, and a visible line saying how to unlock the filters. */
export function WorksQueryResults({ q, tradition = '', onOpen }: WorksQueryResultsProps) {
  const probe = useAsync<Probe | null>(async () => {
    const query = q.trim();
    if (!query) return null;
    const head = await getWorks({
      q: query,
      tradition,
      sort: 'canonical',
      limit: PAGE.facetLimit,
    });
    if (head.total > LIBRARY.assembleMax) return { works: null, total: head.total };
    const { items, total } = await assembleWorks(
      { q: query, tradition, sort: 'canonical' },
      head,
    );
    return { works: items, total };
  }, [q, tradition]);

  return (
    <DataView
      result={probe}
      loadingLabel="Searching the works"
      errorText="Works search is unavailable"
      isEmpty={(data) => data.total === 0}
      emptyText={`No works match “${q.trim()}”. Titles and authors are searched; the Content scope looks inside the books.`}
    >
      {({ works, total }) => (
        <div className="works">
          <Apparatus marginalia={countLabel(total, 'work')}>Works · المصنّفات</Apparatus>
          {works ? (
            <FacetedWorksList works={works} total={total} defaultSort="canonical" onOpen={onOpen} />
          ) : (
            <RankedPages q={q.trim()} tradition={tradition} total={total} onOpen={onOpen} />
          )}
        </div>
      )}
    </DataView>
  );
}

interface RankedPagesProps {
  q: string;
  tradition: string;
  total: number;
  onOpen: (urn: string, page?: number) => void;
}

/** The stated degraded mode for a query too broad to facet: canonical-ranked
    server pages with load-more. The mode announces itself; it never silently
    drops the filters a narrower query would have. */
function RankedPages({ q, tradition, total, onOpen }: RankedPagesProps) {
  const res = usePaged(
    (offset) => getWorks({ q, tradition, sort: 'canonical', limit: LIBRARY.listPageSize, offset }),
    [q, tradition],
  );
  return (
    <>
      <Text as="p" size="sm" tone="muted">
        Too many matches to facet: era and foundational filters come with a query under{' '}
        {formatCount(LIBRARY.assembleMax)} matches. Showing the canonical ranking in pages.
      </Text>
      {res.error ? <ErrorText>Works search is unavailable: {res.error.message}</ErrorText> : null}
      <div className="wrows">
        {res.items.map((w) => (
          <WorkRecord key={w.stem} work={w} onOpen={onOpen} />
        ))}
      </div>
      <LoadMoreFoot
        line={`Showing ${formatCount(res.items.length)} of ${countLabel(total, 'work')}`}
        loading={res.loading}
        spinnerLabel="Loading more works"
        hasMore={res.hasMore}
        onMore={res.more}
      />
    </>
  );
}
