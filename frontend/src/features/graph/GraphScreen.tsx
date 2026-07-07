import { useEffect, useState } from 'react';

import { Heading, Inline, Pager, Segmented, Stack, Text } from '../../lib/design-system';
import { DataView } from '../../lib/DataView';
import { getCanonical, getPerson, getRijal } from '../../lib/api/client';
import { PAGE, REGISTRY } from '../../lib/constants';
import type { Page } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { pageCount } from '../../lib/utils';
import { isCanonical, isPerson, NarratorCard, type NarratorItem } from '../narrators/NarratorCard';
import '../screens.css';

const PER_PAGE = PAGE.graphPerPage;

const TABS = [
  { value: REGISTRY.RIJAL, label: 'Rijāl', icon: 'node' as const },
  { value: REGISTRY.PERSON, label: 'Persons', icon: 'users' as const },
  { value: REGISTRY.CANONICAL, label: 'Canonical', icon: 'layers' as const },
];

function itemKey(item: NarratorItem): string {
  if (isPerson(item)) return `p${item.person_id}`;
  if (isCanonical(item)) return `c${item.canonical_id}`;
  return `r${item.id}`;
}

export function GraphScreen() {
  const [registry, setRegistry] = useState<string>(REGISTRY.RIJAL);
  const [page, setPage] = useState(1);
  const offset = (page - 1) * PER_PAGE;

  useEffect(() => {
    setPage(1);
  }, [registry]);

  const result = useAsync<Page<NarratorItem>>(() => {
    if (registry === REGISTRY.PERSON) return getPerson({ limit: PER_PAGE, offset });
    if (registry === REGISTRY.CANONICAL) return getCanonical({ limit: PER_PAGE, offset });
    return getRijal({ limit: PER_PAGE, offset });
  }, [registry, page]);

  const totalPages = result.data ? pageCount(result.data.total, PER_PAGE) : 1;

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
          stance, and historical events, drawn from the rijāl corpus. Use the header search to find
          a specific narrator or passage.
        </Text>
      </header>

      <Stack gap="md">
        <Inline gap="sm" align="center">
          <Segmented label="Registry" value={registry} options={TABS} onChange={setRegistry} />
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
