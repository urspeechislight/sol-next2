import type { ReactNode } from 'react';

import { Button, Chip, Menu, Segmented, Text } from '../../lib/design-system';
import type { MenuOption } from '../../lib/design-system';
import type { SearchMode } from '../../lib/api/client';
import type { ScopeToken } from '../../lib/taxonomySelection';
import type { CategoryFacet } from '../../lib/types';
import './SearchFilters.css';

const ALL_CATEGORIES = '';
const ALL_BOOKS = '';

/** Individual selection tokens shown before collapsing into "+N more"
    (the popover is the full review surface past this point). */
const TOKEN_CAP = 3;

const MODES = [
  { value: 'exact', label: 'Exact' },
  { value: 'broad', label: 'Partial' },
];

export interface SearchFiltersProps {
  /** Match mode is corpus-only (full-text). Omit it (with onMode) on scopes that
      have no exact/partial distinction, e.g. narrator search. */
  mode?: SearchMode;
  /** A category MENU renders only when a scope passes its facet list (the
      narrator scope's client-derived facets). The content scope selects via
      its map/popover and passes `tokens` instead. */
  categories?: CategoryFacet[];
  labelOf?: (slug: string) => string;
  category?: string;
  /** The collapsed selection: one token per fully-selected domain, then the
      loose categories; shown as removable chips up to TOKEN_CAP. */
  tokens?: ScopeToken[];
  onRemoveToken?: (token: ScopeToken) => void;
  /** Opens the full selection review (the filter popover). */
  onShowAll?: () => void;
  /** The taxonomy picker (funnel button + panel), rendered in the bar. */
  picker?: ReactNode;
  /** The active book filter (stored Arabic title), set by the content
      scope's work-head drill-in; shown as a removable chip. */
  book?: string;
  total: number;
  onMode?: (mode: SearchMode) => void;
  onCategory?: (slug: string) => void;
  onBook?: (title: string) => void;
  onClear?: () => void;
}

/** One unified bar above the results: match mode as a segmented control, the
    taxonomy picker, the active scope as removable chips (collapsing past
    TOKEN_CAP into a "+N more" button that opens the picker), and the result
    count promoted to primary mono feedback. */
export function SearchFilters({
  mode,
  categories = [],
  labelOf = (slug) => slug,
  category = '',
  tokens = [],
  onRemoveToken,
  onShowAll,
  picker,
  book = '',
  total,
  onMode,
  onCategory,
  onBook,
  onClear,
}: SearchFiltersProps) {
  const catOptions: MenuOption[] = [
    { value: ALL_CATEGORIES, label: 'All categories' },
    ...categories.map((c) => ({
      value: c.slug,
      label: `${labelOf(c.slug)} · ${c.count.toLocaleString()}`,
    })),
  ];

  const hasCategory = category !== ALL_CATEGORIES;
  const hasBook = book !== ALL_BOOKS;
  const active = tokens.length > 0 || hasCategory || hasBook;
  const shown = tokens.slice(0, TOKEN_CAP);
  const overflow = tokens.length - shown.length;

  return (
    <div className="search-filters">
      {mode !== undefined ? (
        <>
          <Segmented
            label="Match mode"
            value={mode}
            options={MODES}
            onChange={(v) => onMode?.(v as SearchMode)}
          />
          <span className="search-filters__sep" aria-hidden="true" />
        </>
      ) : null}
      {picker}
      <div className="search-filters__cascade">
        {shown.map((t) => (
          <Chip key={`${t.kind}:${t.id}`} icon="layers" onRemove={() => onRemoveToken?.(t)}>
            {t.label}
          </Chip>
        ))}
        {overflow > 0 ? (
          <Button variant="link" onClick={() => onShowAll?.()}>
            +{overflow.toLocaleString()} more
          </Button>
        ) : null}
        {hasCategory ? (
          <Chip icon="layers" onRemove={() => onCategory?.(ALL_CATEGORIES)}>
            {labelOf(category)}
          </Chip>
        ) : categories.length ? (
          <Menu
            value={category}
            options={catOptions}
            ariaLabel="Filter by category"
            onChange={(s) => onCategory?.(s)}
          />
        ) : null}
        {hasBook ? (
          <Chip icon="book" onRemove={() => onBook?.(ALL_BOOKS)}>
            <span dir="rtl">{book}</span>
          </Chip>
        ) : null}
      </div>
      <span className="search-filters__count">
        <Text as="span" size="md" font="mono" weight="semibold">
          {total.toLocaleString()}
        </Text>
        <Text as="span" size="xs" tone="muted">
          {total === 1 ? 'result' : 'results'}
        </Text>
      </span>
      {active ? (
        <Button variant="link" onClick={() => onClear?.()}>
          Clear all
        </Button>
      ) : null}
    </div>
  );
}
