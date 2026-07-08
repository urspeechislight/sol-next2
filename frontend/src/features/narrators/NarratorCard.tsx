// NarratorCard.tsx:the one narrator-record card, shared by the Graph browser
// and the narrator search scope. Renders a rijāl OR enriched person entry as
// name + tradition + a kind-specific meta row; a person card also expands into
// a detail drawer (identity, teachers, students, sources, grades, bio).
import { useState } from 'react';

import { Badge, Card, Heading, Inline, Stack, Text, UnstyledButton } from '../../lib/design-system';
import type { PersonEntry, RijalEntry } from '../../lib/types';
import { joinDots } from '../../lib/utils';
import { reliabilityBadge } from '../../lib/variants';
import { generationLabel, residenceLabel, stanceLabel, traditionLabel } from './labels';
import { PersonDrawer } from './PersonDrawer';

export type NarratorItem = RijalEntry | PersonEntry;

/** Opens a source book at a page with a highlight term (App's reader opener),
    threaded to the grade rows in the person drawer. */
type OpenReader = (urn: string, page: number, query: string) => void;

/** True when a narrator item is an enriched person record (vs a raw rijāl entry). */
export function isPerson(item: NarratorItem): item is PersonEntry {
  return 'person_id' in item;
}

function RijalMeta({ entry }: { entry: RijalEntry }) {
  return (
    <Inline gap="xs" align="center">
      {entry.reliability_term ? (
        <Badge variant={reliabilityBadge(entry.reliability_term)}>
          <span dir="rtl">{entry.reliability_term}</span>
        </Badge>
      ) : null}
      <Text size="xs" tone="faint" font="mono">
        {entry.teacher_count} teachers · {entry.student_count} students
      </Text>
      {entry.source_label ? (
        <Text size="xs" tone="faint">
          {entry.source_label}
        </Text>
      ) : null}
    </Inline>
  );
}

function PersonMeta({ entry }: { entry: PersonEntry }) {
  const topGrade = entry.reliability[0]?.split('=')[1] ?? '';
  const residence = entry.places ? residenceLabel(entry.places) : '';
  const facts = [
    entry.death_year ? `d. ${entry.death_year} AH` : '',
    residence,
    `${entry.teacher_count} teachers · ${entry.student_count} students`,
    `${entry.n_sources} sources`,
    entry.event_count ? `${entry.event_count} events` : '',
  ]
    .filter(Boolean)
    .join(' · ');
  return (
    <Inline gap="xs" align="center">
      {entry.generation ? (
        <Badge variant="success">{generationLabel(entry.generation)}</Badge>
      ) : null}
      {topGrade ? (
        <Badge variant={reliabilityBadge(topGrade)}>
          <span dir="rtl">{topGrade}</span>
        </Badge>
      ) : null}
      {entry.stance ? <Badge>{stanceLabel(entry.stance)}</Badge> : null}
      <Text size="xs" tone="faint" font="mono">
        {facts}
      </Text>
    </Inline>
  );
}

/** One narrator record card (rijāl or person): name + tradition + meta + detail. */
export function NarratorCard({
  item,
  onOpenReader,
}: {
  item: NarratorItem;
  onOpenReader: OpenReader;
}) {
  const [open, setOpen] = useState(false);
  const sub = joinDots(item.kunya, item.nisba);
  const person = isPerson(item);
  const latin = isPerson(item) ? item.name_latin : '';
  return (
    <Card variant="flat" pad="md">
      <Stack gap="xs">
        <Inline gap="sm" align="start" justify="between">
          <Stack gap="xs">
            {latin ? (
              <Text size="sm" weight="semibold">
                {latin}
              </Text>
            ) : null}
            <Heading level={4} font="arabic" dir="rtl">
              {item.full_name}
            </Heading>
          </Stack>
          {item.tradition ? <Badge>{traditionLabel(item.tradition)}</Badge> : null}
        </Inline>
        {sub ? (
          <Text size="sm" tone="muted" font="arabic" dir="rtl">
            {sub}
          </Text>
        ) : null}
        {person ? <PersonMeta entry={item} /> : <RijalMeta entry={item} />}
        {person ? (
          <UnstyledButton onClick={() => setOpen((value) => !value)}>
            <Text size="xs" tone="accent">
              {open ? 'Hide detail' : 'Show identity, teachers, students, sources, grades'}
            </Text>
          </UnstyledButton>
        ) : null}
        {person && open ? <PersonDrawer entry={item} onOpenReader={onOpenReader} /> : null}
      </Stack>
    </Card>
  );
}
