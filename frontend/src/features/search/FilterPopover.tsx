import { useCallback, useRef } from 'react';

import { Button, Checkbox, useDismiss } from '../../lib/design-system';
import { countLabel } from '../library/lib';
import { groupState } from '../../lib/taxonomySelection';
import type { FacetRollup } from './facetRollup';
import './FilterPopover.css';

export interface FilterPopoverProps {
  /** The query's distribution, grouped by domain (true counts). */
  rollup: FacetRollup;
  selected: ReadonlySet<string>;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  labelOf: (slug: string) => string;
  onToggleGroup: (slugs: readonly string[]) => void;
  onToggleCategory: (slug: string) => void;
  onClearCategories: () => void;
}

/** The funnel button and its anchored panel: the WHOLE matching taxonomy at
    once (every domain group with its categories and true counts) for
    reviewing and bulk-editing a cross-domain selection the map chips can
    only build one domain at a time. Strictly a second view of the same
    selection set the map writes; it holds no state of its own. */
export function FilterPopover({
  rollup,
  selected,
  open,
  onOpenChange,
  labelOf,
  onToggleGroup,
  onToggleCategory,
  onClearCategories,
}: FilterPopoverProps) {
  const root = useRef<HTMLDivElement>(null);
  const close = useCallback(() => onOpenChange(false), [onOpenChange]);
  useDismiss(root, open, close);
  const boxState = (state: 'none' | 'partial' | 'all'): boolean | 'mixed' =>
    state === 'all' ? true : state === 'partial' ? 'mixed' : false;

  return (
    <div ref={root} className="fpop">
      <Button
        variant="secondary"
        size="sm"
        iconBefore="filter"
        ariaLabel={
          selected.size > 0
            ? `Filter by category, ${countLabel(selected.size, 'category', 'categories')} selected`
            : 'Filter by category'
        }
        onClick={() => onOpenChange(!open)}
      >
        Filter{selected.size > 0 ? ` · ${selected.size}` : ''}
      </Button>
      {open ? (
        <div className="fpop__panel" role="group" aria-label="Filter by domain and category">
          {rollup.domains.map((d) => {
            const slugs = d.categories.map((c) => c.slug);
            return (
              <section key={d.id} className="fpop__group">
                <Checkbox
                  checked={boxState(groupState(slugs, selected))}
                  onToggle={() => onToggleGroup(slugs)}
                  count={d.count}
                  ariaLabel={`All ${d.label} categories`}
                >
                  <span className="fpop__domain">{d.label}</span>
                </Checkbox>
                <div className="fpop__cats">
                  {d.categories.map((c) => (
                    <Checkbox
                      key={c.slug}
                      checked={selected.has(c.slug)}
                      onToggle={() => onToggleCategory(c.slug)}
                      count={c.count}
                    >
                      {labelOf(c.slug)}
                    </Checkbox>
                  ))}
                </div>
              </section>
            );
          })}
          {rollup.unmatched.map((f) => (
            <Checkbox
              key={f.slug}
              checked={selected.has(f.slug)}
              onToggle={() => onToggleCategory(f.slug)}
              count={f.count}
            >
              {labelOf(f.slug)}
            </Checkbox>
          ))}
          {selected.size > 0 ? (
            <footer className="fpop__foot">
              <Button variant="link" onClick={onClearCategories}>
                Clear categories
              </Button>
            </footer>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
