import { useState } from 'react';

import {
  Heading,
  Inline,
  Input,
  Menu,
  Pager,
  Segmented,
  Stack,
  Text,
} from '../../lib/design-system';
import type { MenuOption } from '../../lib/design-system';
import { DataView } from '../../lib/DataView';
import { getPerson, getRijal } from '../../lib/api/client';
import { PAGE, REGISTRY } from '../../lib/constants';
import type { Page } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { formatCount, pageCount, pluralNoun } from '../../lib/utils';
import { TRADITION_OPTIONS } from '../narrators/labels';
import { isPerson, NarratorCard, type NarratorItem } from '../narrators/NarratorCard';
import '../screens.css';

const PER_PAGE = PAGE.graphPerPage;

/** The registry browser's committed state. Lifted to App (not held locally) so it
    survives the reader takeover: opening a source book unmounts this screen, and
    without lifting, Back would remount it reset to page 1 with filters cleared. */
export interface GraphState {
  registry: string;
  page: number;
  q: string;
  tradition: string;
  category: string;
}

/** The initial registry browse state, spread by App's useState initializer. */
export const EMPTY_GRAPH: GraphState = {
  registry: REGISTRY.RIJAL,
  page: 1,
  q: '',
  tradition: '',
  category: '',
};

const TABS = [
  { value: REGISTRY.RIJAL, label: 'Rijāl', icon: 'node' as const },
  { value: REGISTRY.PERSON, label: 'Persons', icon: 'users' as const },
];

/** Tradition applies to both registries; the backend filters server-side on these tokens. */
const TRADITIONS: MenuOption[] = [{ value: '', label: 'All traditions' }, ...TRADITION_OPTIONS];

/** Rijāl entry data-quality class. */
const CATEGORIES: MenuOption[] = [
  { value: '', label: 'All entries' },
  { value: 'clean', label: 'Clean' },
  { value: 'long_entry', label: 'Long entry' },
  { value: 'editorial', label: 'Editorial' },
  { value: 'isnad_fragment', label: 'Isnād fragment' },
  { value: 'ref_number', label: 'Reference' },
];

function itemKey(item: NarratorItem): string {
  return isPerson(item) ? `p${item.person_id}` : `r${item.id}`;
}

interface GraphScreenProps {
  state: GraphState;
  onState: (next: GraphState) => void;
  onOpenReader: (urn: string, page: number, query: string) => void;
}

export function GraphScreen({ state, onState, onOpenReader }: GraphScreenProps) {
  const { registry, page, q, tradition, category } = state;
  const [draft, setDraft] = useState(q);
  const offset = (page - 1) * PER_PAGE;
  const persons = registry === REGISTRY.PERSON;

  const setRegistry = (value: string) => onState({ ...state, registry: value, page: 1 });
  const setTradition = (value: string) => onState({ ...state, tradition: value, page: 1 });
  const setCategory = (value: string) => onState({ ...state, category: value, page: 1 });
  const submitQuery = () => onState({ ...state, q: draft, page: 1 });
  const setPage = (value: number) => onState({ ...state, page: value });
  const clearSearch = () => {
    setDraft('');
    onState({ ...state, q: '', page: 1 });
  };

  const result = useAsync<Page<NarratorItem>>(() => {
    if (persons) return getPerson({ q, tradition, limit: PER_PAGE, offset });
    return getRijal({ q, tradition, category, limit: PER_PAGE, offset });
  }, [registry, page, q, tradition, category]);

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
          reliability-graded narrators and enriched person identities with death years and
          historical events, drawn from the rijāl corpus. Search by name and filter by tradition
          or entry class.
        </Text>
      </header>

      <Stack gap="md">
        <Inline gap="sm" align="center">
          <Segmented label="Registry" value={registry} options={TABS} onChange={setRegistry} />
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
          {persons ? null : (
            <Menu
              value={category}
              options={CATEGORIES}
              ariaLabel="Filter by entry class"
              onChange={setCategory}
            />
          )}
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
        >
          {(data) => (
            <>
              <Stack gap="sm">
                {data.items.map((item) => (
                  <NarratorCard key={itemKey(item)} item={item} onOpenReader={onOpenReader} />
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
