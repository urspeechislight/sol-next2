import { useMemo, useState } from 'react';
import { Apparatus } from '../../lib/design-system';
import { LoadMoreFoot } from '../../lib/LoadMoreFoot';
import { LIBRARY } from '../../lib/constants';
import type { Work } from '../../lib/types';
import { countLabel, formatCount } from '../../lib/utils';
import { FilterBar } from './FilterBar';
import { WorkRecord } from './WorkRecord';
import { groupByEra } from './lib';
import { DEFAULT_FILTERS, applyFilters } from './worksFilter';
import type { Filters, SortMode } from './worksFilter';

export interface FacetedWorksListProps {
  /** The whole assembled scope: filters facet it truthfully. */
  works: Work[];
  /** The server's total for the scope (the foot states it when fetch < total). */
  total: number;
  /** Starting sort: 'era' for browsing rooms, 'canonical' for search results. */
  defaultSort?: SortMode;
  onOpen: (urn: string, page?: number) => void;
}

/** One honest faceted list over an assembled scope, the grammar shared by the
    category room and the works search: the FilterBar's combinable facets, the
    era-section or flat ordering, load-more windowing, and the foot that always
    states how much of what is on screen. */
export function FacetedWorksList({
  works,
  total,
  defaultSort = DEFAULT_FILTERS.sort,
  onOpen,
}: FacetedWorksListProps) {
  const [filters, setFilters] = useState<Filters>({ ...DEFAULT_FILTERS, sort: defaultSort });
  const [shown, setShown] = useState<number>(LIBRARY.listPageSize);
  const changeFilters = (next: Filters) => {
    setFilters(next);
    setShown(LIBRARY.listPageSize);
  };

  const filtered = useMemo(() => applyFilters(works, filters), [works, filters]);
  const visible = filtered.slice(0, shown);

  return (
    <>
      <FilterBar works={works} filters={filters} onChange={changeFilters} />
      {filters.sort === 'era' ? (
        <EraSections works={visible} onOpen={onOpen} allFiltered={filtered} />
      ) : (
        <div className="wrows">
          {visible.map((w) => (
            <WorkRecord key={w.stem} work={w} onOpen={onOpen} />
          ))}
        </div>
      )}
      <ListFoot
        shown={visible.length}
        matched={filtered.length}
        fetched={works.length}
        total={total}
        onMore={() => setShown((n) => n + LIBRARY.listPageSize)}
      />
    </>
  );
}

interface EraSectionsProps {
  /** The windowed slice actually rendered. */
  works: Work[];
  /** The full filtered list, for true per-century counts on the rules. */
  allFiltered: Work[];
  onOpen: (urn: string) => void;
}

/** The era-ordered list as open century sections: each century head is an
    apparatus rule carrying the century's TRUE count (the window may cut a
    century short; the rule never lies about its size). */
function EraSections({ works, allFiltered, onOpen }: EraSectionsProps) {
  const fullCounts = useMemo(
    () => new Map(groupByEra(allFiltered).map((g) => [g.century, g.works.length])),
    [allFiltered],
  );
  const groups = groupByEra(works);
  return (
    <div className="cpane__eras">
      {groups.map((g) => (
        <section key={g.century} className="cpane__era">
          <Apparatus marginalia={formatCount(fullCounts.get(g.century) ?? g.works.length)}>
            {g.labelEn} · {g.labelAr}
          </Apparatus>
          <div className="wrows">
            {g.works.map((w) => (
              <WorkRecord key={w.stem} work={w} onOpen={onOpen} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

interface ListFootProps {
  shown: number;
  matched: number;
  fetched: number;
  total: number;
  onMore: () => void;
}

/** The honesty line + load-more: always says how much of what is on screen. */
function ListFoot({ shown, matched, fetched, total, onMore }: ListFootProps) {
  const line =
    `Showing ${formatCount(shown)} of ${formatCount(matched)}` +
    (matched !== fetched ? ` matching (${formatCount(fetched)} in scope)` : '') +
    (fetched < total ? ` · ${countLabel(total, 'work')} on the server` : '');
  return <LoadMoreFoot line={line} hasMore={shown < matched} onMore={onMore} />;
}
