import { Button, Spinner, Text } from '../../lib/design-system';
import { getWorks } from '../../lib/api/client';
import { LIBRARY, PAGE } from '../../lib/constants';
import type { Work } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { usePaged } from '../../lib/usePaged';
import { Apparatus } from './Apparatus';
import { FacetedWorksList } from './FacetedWorksList';
import { WorkRecord } from './WorkRecord';
import { countLabel } from './lib';

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
    const first = await getWorks({
      q: query,
      tradition,
      sort: 'canonical',
      limit: PAGE.facetLimit,
    });
    if (first.total > LIBRARY.assembleMax) return { works: null, total: first.total };
    const items = [...first.items];
    while (items.length < first.total) {
      const next = await getWorks({
        q: query,
        tradition,
        sort: 'canonical',
        limit: PAGE.facetLimit,
        offset: items.length,
      });
      if (next.items.length === 0) break;
      items.push(...next.items);
    }
    return { works: items, total: first.total };
  }, [q, tradition]);

  if (probe.loading) return <Spinner label="Searching the works" />;
  if (probe.error) {
    return (
      <Text as="p" size="sm" tone="danger">
        Works search is unavailable: {probe.error.message}
      </Text>
    );
  }
  if (!probe.data) return null;

  const { works, total } = probe.data;
  if (total === 0) {
    return (
      <Text as="p" size="sm" tone="muted">
        No works match “{q.trim()}”. Titles and authors are searched; the Content scope looks inside
        the books.
      </Text>
    );
  }
  return (
    <div className="works">
      <Apparatus marginalia={countLabel(total, 'work')}>Works · المصنّفات</Apparatus>
      {works ? (
        <FacetedWorksList works={works} total={total} defaultSort="canonical" onOpen={onOpen} />
      ) : (
        <RankedPages q={q.trim()} tradition={tradition} total={total} onOpen={onOpen} />
      )}
    </div>
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
        {LIBRARY.assembleMax.toLocaleString()} matches. Showing the canonical ranking in pages.
      </Text>
      {res.error ? (
        <Text as="p" size="sm" tone="danger">
          Works search is unavailable: {res.error.message}
        </Text>
      ) : null}
      <div className="wrows">
        {res.items.map((w) => (
          <WorkRecord key={w.stem} work={w} onOpen={onOpen} />
        ))}
      </div>
      <footer className="cpane__foot">
        <Text size="xs" tone="faint" font="mono">
          Showing {res.items.length.toLocaleString()} of {countLabel(total, 'work')}
        </Text>
        {res.loading ? <Spinner label="Loading more works" /> : null}
        {!res.loading && res.hasMore ? (
          <Button variant="secondary" size="sm" onClick={res.more}>
            Show more
          </Button>
        ) : null}
      </footer>
    </>
  );
}
