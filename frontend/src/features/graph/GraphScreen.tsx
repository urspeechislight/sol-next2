import { useState } from 'react';

import { Heading, Inline, Input, Menu, Pager, Stack, Text } from '../../lib/design-system';
import type { MenuOption } from '../../lib/design-system';
import { DataView } from '../../lib/DataView';
import { getNarrators } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import type { NarratorEntry, Page } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { formatCount, pageCount, pluralNoun } from '../../lib/utils';
import { CATEGORY_OPTIONS, TRADITION_OPTIONS } from '../narrators/labels';
import { NarratorCard } from '../narrators/NarratorCard';
import '../screens.css';

const PER_PAGE = PAGE.graphPerPage;

/** The registry browser's committed state. Lifted to App (not held locally) so it
    survives the reader takeover: opening a source book unmounts this screen, and
    without lifting, Back would remount it reset to page 1 with filters cleared. */
export interface GraphState {
  page: number;
  q: string;
  tradition: string;
  category: string;
}

/** The initial registry browse state, spread by App's useState initializer. */
export const EMPTY_GRAPH: GraphState = {
  page: 1,
  q: '',
  tradition: '',
  category: '',
};

/** Tradition and entry class filter server-side on these tokens. */
const TRADITIONS: MenuOption[] = [{ value: '', label: 'All traditions' }, ...TRADITION_OPTIONS];

const CATEGORIES: MenuOption[] = [{ value: '', label: 'All entries' }, ...CATEGORY_OPTIONS];

interface GraphScreenProps {
  state: GraphState;
  onState: (next: GraphState) => void;
}

export function GraphScreen({ state, onState }: GraphScreenProps) {
  const { page, q, tradition, category } = state;
  const [draft, setDraft] = useState(q);
  const offset = (page - 1) * PER_PAGE;

  const setTradition = (value: string) => onState({ ...state, tradition: value, page: 1 });
  const setCategory = (value: string) => onState({ ...state, category: value, page: 1 });
  const submitQuery = () => onState({ ...state, q: draft, page: 1 });
  const setPage = (value: number) => onState({ ...state, page: value });
  const clearSearch = () => {
    setDraft('');
    onState({ ...state, q: '', page: 1 });
  };

  const result = useAsync<Page<NarratorEntry>>(
    () => getNarrators({ q, tradition, category, limit: PER_PAGE, offset }),
    [page, q, tradition, category],
  );

  const totalPages = result.data ? pageCount(result.data.total, PER_PAGE) : 1;

  return (
    <section>
      <header className="scr__head">
        <Text size="xs" tone="accent" weight="semibold" className="scr__eyebrow">
          Narrators · الرجال
        </Text>
        <Heading level={1}>Transmission registry</Heading>
        <Text as="p" size="md" tone="muted" className="scr__lede">
          {result.data ? `${formatCount(result.data.total)} ` : ''}
          narrators with their recorded names, reliability gradings, and teacher–student relations,
          drawn from the rijāl corpus. Search by name and filter by tradition or entry class; open a
          card for its gradings and tarjama, or its transmission graph.
        </Text>
      </header>

      <Stack gap="md">
        <Inline gap="sm" align="center">
          <Input
            type="search"
            icon="search"
            value={draft}
            placeholder="Search narrators by name…"
            ariaLabel="Search narrators by name"
            onInput={setDraft}
            onSubmit={submitQuery}
            onClear={clearSearch}
            clearLabel="Clear search"
          />
        </Inline>

        <Inline gap="sm" align="center">
          <Menu
            value={tradition}
            options={TRADITIONS}
            ariaLabel="Filter by tradition"
            onChange={setTradition}
          />
          <Menu
            value={category}
            options={CATEGORIES}
            ariaLabel="Filter by entry class"
            onChange={setCategory}
          />
          {result.data ? (
            <Text size="sm" tone="muted" font="mono" weight="semibold">
              {`${formatCount(result.data.total)} ${pluralNoun(result.data.total, 'narrator')}`}
            </Text>
          ) : null}
        </Inline>

        <DataView
          result={result}
          loadingLabel="Loading narrators"
          errorText="Could not load the registry"
          isEmpty={(data) => data.items.length === 0}
          emptyText="No narrators match these filters."
        >
          {(data) => (
            <>
              <Stack gap="sm">
                {data.items.map((item) => (
                  <NarratorCard key={item.id} item={item} />
                ))}
              </Stack>
              <Pager page={page} totalPages={totalPages} onPage={setPage} />
            </>
          )}
        </DataView>
      </Stack>
    </section>
  );
}
