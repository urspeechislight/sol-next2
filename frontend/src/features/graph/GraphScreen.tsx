import { useEffect, useState } from 'react';

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
import { isPerson, NarratorCard, type NarratorItem } from '../narrators/NarratorCard';
import '../screens.css';

const PER_PAGE = PAGE.graphPerPage;

const TABS = [
  { value: REGISTRY.RIJAL, label: 'Rijāl', icon: 'node' as const },
  { value: REGISTRY.PERSON, label: 'Persons', icon: 'users' as const },
];

/** Tradition applies to both registries; the backend filters server-side on these tokens. */
const TRADITIONS: MenuOption[] = [
  { value: '', label: 'All traditions' },
  { value: 'sunni', label: 'Sunnī' },
  { value: 'shia', label: 'Shīʿī' },
  { value: 'both', label: 'Sunnī + Shīʿī' },
  { value: 'history', label: 'History' },
];

/** Person stance vis-à-vis the Ahl al-Bayt (only a minority of narrators are evaluated). */
const STANCES: MenuOption[] = [
  { value: '', label: 'Any stance' },
  { value: 'ahlulbayt_member', label: 'Ahl al-Bayt' },
  { value: 'pro_ahlulbayt', label: 'Pro-Ahl al-Bayt' },
  { value: 'anti_ahlulbayt', label: 'Anti-Ahl al-Bayt' },
  { value: 'khariji', label: 'Khārijī' },
];

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

export function GraphScreen() {
  const [registry, setRegistry] = useState<string>(REGISTRY.RIJAL);
  const [page, setPage] = useState(1);
  const [draft, setDraft] = useState('');
  const [q, setQ] = useState('');
  const [tradition, setTradition] = useState('');
  const [stance, setStance] = useState('');
  const [category, setCategory] = useState('');
  const offset = (page - 1) * PER_PAGE;
  const persons = registry === REGISTRY.PERSON;

  useEffect(() => {
    setPage(1);
  }, [registry, q, tradition, stance, category]);

  const result = useAsync<Page<NarratorItem>>(() => {
    if (persons) return getPerson({ q, tradition, stance, limit: PER_PAGE, offset });
    return getRijal({ q, tradition, category, limit: PER_PAGE, offset });
  }, [registry, page, q, tradition, stance, category]);

  const totalPages = result.data ? pageCount(result.data.total, PER_PAGE) : 1;

  const clearSearch = () => {
    setDraft('');
    setQ('');
  };

  return (
    <section>
      <header className="scr__head">
        <Text size="xs" tone="accent" weight="semibold" className="scr__eyebrow">
          Narrators · الرجال
        </Text>
        <Heading level={1}>Transmission registry</Heading>
        <Text as="p" size="md" tone="muted" className="scr__lede">
          {result.data ? `${result.data.total.toLocaleString()} ` : ''}
          reliability-graded narrators and enriched person identities with death years, ahlulbayt
          stance, and historical events, drawn from the rijāl corpus. Search by name and filter by
          tradition, stance, or entry class.
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
            onSubmit={() => setQ(draft)}
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
          {persons ? (
            <Menu
              value={stance}
              options={STANCES}
              ariaLabel="Filter by ahlulbayt stance"
              onChange={setStance}
            />
          ) : (
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
                  <NarratorCard key={itemKey(item)} item={item} />
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
