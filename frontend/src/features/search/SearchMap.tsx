import { useState } from 'react';

import { FacetChip } from '../../lib/design-system';
import { countLabel } from '../library/lib';
import { Apparatus } from '../library/Apparatus';
import { groupState } from '../../lib/taxonomySelection';
import type { FacetRollup } from './facetRollup';
import './SearchMap.css';

export interface SearchMapProps {
  /** The query's distribution, grouped by domain (true counts, query-global:
      the map is the atlas of the PHRASE; the toolbar count is the stream). */
  rollup: FacetRollup;
  /** How many categories hold matches (the apparatus marginalia). */
  categoriesCount: number;
  /** The one selection set (shared with the filter popover). */
  selected: ReadonlySet<string>;
  labelOf: (slug: string) => string;
  onToggleGroup: (slugs: readonly string[]) => void;
  onToggleCategory: (slug: string) => void;
}

/** The distribution map as the selection's fast path: domain chips carry
    TRUE summed counts and toggle their whole domain (half-pressed when only
    some of its categories are selected); the last-touched domain discloses
    its categories as a subordinate row of additive toggles. Cross-domain
    review and bulk edits live in the filter popover, a second view of the
    SAME set. Renders nothing when the server dropped the facets at its scan
    cap; the caller states that honestly instead. */
export function SearchMap({
  rollup,
  categoriesCount,
  selected,
  labelOf,
  onToggleGroup,
  onToggleCategory,
}: SearchMapProps) {
  const [openDomain, setOpenDomain] = useState('');
  if (categoriesCount === 0) return null;
  const open = rollup.domains.find((d) => d.id === openDomain);
  return (
    <section className="smap" aria-label="Matches by domain">
      <Apparatus marginalia={countLabel(categoriesCount, 'category', 'categories')}>
        Found across · مواضع الورود
      </Apparatus>
      <div className="smap__row" role="group" aria-label="Filter by domain">
        {rollup.domains.map((d) => {
          const slugs = d.categories.map((c) => c.slug);
          const state = groupState(slugs, selected);
          return (
            <FacetChip
              key={d.id}
              label={d.label}
              count={d.count}
              on={state === 'all'}
              partial={state === 'partial'}
              onToggle={() => {
                setOpenDomain(d.id);
                onToggleGroup(slugs);
              }}
              ariaLabel={`Toggle all ${d.label}, ${countLabel(d.count, 'passage')}`}
            />
          );
        })}
        {rollup.unmatched.map((f) => (
          <FacetChip
            key={f.slug}
            label={labelOf(f.slug)}
            count={f.count}
            on={selected.has(f.slug)}
            onToggle={() => onToggleCategory(f.slug)}
            ariaLabel={`Toggle ${labelOf(f.slug)}, ${countLabel(f.count, 'passage')}`}
          />
        ))}
      </div>
      {open ? (
        <div className="smap__sub" role="group" aria-label={`Categories within ${open.label}`}>
          {open.categories.map((c) => (
            <FacetChip
              key={c.slug}
              label={labelOf(c.slug)}
              count={c.count}
              on={selected.has(c.slug)}
              onToggle={() => onToggleCategory(c.slug)}
              ariaLabel={`Toggle ${labelOf(c.slug)}, ${countLabel(c.count, 'passage')}`}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}
