import { FacetChip, Input, Menu } from '../../lib/design-system';
import type { Work } from '../../lib/types';
import { groupByEra } from './lib';
import { SORT_OPTIONS } from './worksFilter';
import type { Filters, SortMode } from './worksFilter';
import './FilterBar.css';

export interface FilterBarProps {
  /** The whole scope, unfiltered: the era chips carry its true counts. */
  works: Work[];
  filters: Filters;
  onChange: (next: Filters) => void;
}

/** The works browse controls: the era spread as FacetChips with true counts
    (undated included as a first-class chip), an author filter, a foundational
    toggle, and an explicit sort. Facets combine; none of them is a separate
    "view". */
export function FilterBar({ works, filters, onChange }: FilterBarProps) {
  const eras = groupByEra(works);
  const set = (patch: Partial<Filters>) => onChange({ ...filters, ...patch });
  return (
    <div className="fbar">
      <div className="fbar__eras" role="group" aria-label="Filter by century">
        {eras.map((e) => {
          const active = filters.era === e.century;
          return (
            <FacetChip
              key={e.century}
              label={e.labelEn.replace(' century AH', ' c.')}
              count={e.works.length}
              on={active}
              onToggle={() => set({ era: active ? null : e.century })}
              ariaLabel={`${e.labelEn}, ${e.works.length} works`}
            />
          );
        })}
      </div>
      <div className="fbar__row">
        <Input
          value={filters.author}
          type="search"
          icon="users"
          placeholder="Filter by author…"
          ariaLabel="Filter by author"
          className="fbar__author"
          onInput={(v) => set({ author: v })}
        />
        <FacetChip
          label={
            <>
              <span aria-hidden="true">✻</span> Foundational
            </>
          }
          on={filters.foundational}
          onToggle={() => set({ foundational: !filters.foundational })}
          ariaLabel="Only foundational works"
        />
        <span className="fbar__spacer" />
        <Menu
          value={filters.sort}
          options={SORT_OPTIONS}
          ariaLabel="Sort works"
          onChange={(v) => set({ sort: v as SortMode })}
        />
      </div>
    </div>
  );
}
