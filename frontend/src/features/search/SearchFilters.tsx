import { Button, Chip, Icon, Menu, Segmented, Text } from '../../lib/design-system';
import type { MenuOption } from '../../lib/design-system';
import type { SearchMode } from '../../lib/api/client';
import type { BookFacet, CategoryFacet, VolumeFacet } from '../../lib/types';
import './SearchFilters.css';

const ALL_CATEGORIES = '';
const ALL_BOOKS = '';
const ALL_VOLUMES = 0;
const MIN_VOLUMES = 2;

const MODES = [
  { value: 'exact', label: 'Exact' },
  { value: 'broad', label: 'Sub-phrases' },
];

export interface SearchFiltersProps {
  /** Match mode is corpus-only (full-text). Omit it (with onMode) on scopes that
      have no exact/sub-phrase distinction, e.g. book or narrator search. */
  mode?: SearchMode;
  /** A count-only scope (e.g. a Qurʾān term search) omits the category level
      entirely and the bar shows just the promoted count. */
  categories?: CategoryFacet[];
  /** The book + volume cascade levels are corpus-only (they come from the server
      facet endpoint). Scopes that only filter by category omit them. */
  books?: BookFacet[];
  volumes?: VolumeFacet[];
  labelOf?: (slug: string) => string;
  category?: string;
  book?: string;
  volume?: number;
  total: number;
  onMode?: (mode: SearchMode) => void;
  onCategory?: (slug: string) => void;
  onBook?: (title: string) => void;
  onVolume?: (volume: number) => void;
  onClear?: () => void;
}

function Chevron() {
  return (
    <span className="search-filters__chevron" aria-hidden="true">
      <Icon name="chevron-right" size="sm" />
    </span>
  );
}

/** One unified bar above the results. Match mode is a segmented control; the
    source cascade (category -> book -> volume) reads left to right with chevrons,
    each active level a removable chip and each open level a styled menu, never a
    native dropdown. The result count is promoted to primary mono feedback. */
export function SearchFilters({
  mode,
  categories = [],
  books = [],
  volumes = [],
  labelOf = (slug) => slug,
  category = '',
  book = '',
  volume = 0,
  total,
  onMode,
  onCategory,
  onBook,
  onVolume,
  onClear,
}: SearchFiltersProps) {
  const catOptions: MenuOption[] = [
    { value: ALL_CATEGORIES, label: 'All categories' },
    ...categories.map((c) => ({
      value: c.slug,
      label: `${labelOf(c.slug)} · ${c.count.toLocaleString()}`,
    })),
  ];
  const bookOptions: MenuOption[] = [
    { value: ALL_BOOKS, label: 'All books' },
    ...books.map((b) => ({
      value: b.title,
      label: `${b.title_en ?? b.title} · ${b.count.toLocaleString()}`,
    })),
  ];
  const volOptions: MenuOption[] = [
    { value: String(ALL_VOLUMES), label: 'All volumes' },
    ...volumes.map((v) => ({
      value: String(v.volume),
      label: `Vol. ${v.volume} · ${v.count.toLocaleString()}`,
    })),
  ];

  const hasCategory = category !== ALL_CATEGORIES;
  const hasBook = book !== ALL_BOOKS;
  const hasVolume = volume !== ALL_VOLUMES;
  const showBooks = hasCategory && books.length > 0;
  const showVolumes = hasBook && volumes.length >= MIN_VOLUMES;
  const active = hasCategory || hasBook || hasVolume;
  const bookLabel = books.find((b) => b.title === book)?.title_en ?? book;

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
      <div className="search-filters__cascade">
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
        {showBooks ? (
          <>
            <Chevron />
            {hasBook ? (
              <Chip onRemove={() => onBook?.(ALL_BOOKS)}>{bookLabel}</Chip>
            ) : (
              <Menu
                value={book}
                options={bookOptions}
                ariaLabel="Filter by book"
                onChange={(t) => onBook?.(t)}
              />
            )}
          </>
        ) : null}
        {showVolumes ? (
          <>
            <Chevron />
            {hasVolume ? (
              <Chip onRemove={() => onVolume?.(ALL_VOLUMES)}>Vol. {volume}</Chip>
            ) : (
              <Menu
                value={String(volume)}
                options={volOptions}
                ariaLabel="Filter by volume"
                onChange={(v) => onVolume?.(Number(v))}
              />
            )}
          </>
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
