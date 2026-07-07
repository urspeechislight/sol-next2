// NarratorCard.tsx:the one narrator-record card, shared by the Graph browser
// and the narrator search scope. Renders a rijāl OR enriched person entry as
// name + tradition + a kind-specific meta row, so the two surfaces stay
// identical instead of each hand-rolling a near-copy.
import { Badge, Card, Heading, Inline, Stack, Text } from '../../lib/design-system';
import type { PersonEntry, RijalEntry } from '../../lib/types';
import { joinDots } from '../../lib/utils';
import { reliabilityBadge } from '../../lib/variants';

export type NarratorItem = RijalEntry | PersonEntry;

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
  const facts = [
    entry.death_year ? `d. ${entry.death_year} AH` : '',
    `${entry.n_sources} sources`,
    entry.event_count ? `${entry.event_count} events` : '',
  ]
    .filter(Boolean)
    .join(' · ');
  return (
    <Inline gap="xs" align="center">
      {topGrade ? (
        <Badge variant={reliabilityBadge(topGrade)}>
          <span dir="rtl">{topGrade}</span>
        </Badge>
      ) : null}
      {entry.stance ? <Badge>{entry.stance}</Badge> : null}
      <Text size="xs" tone="faint" font="mono">
        {facts}
      </Text>
    </Inline>
  );
}

/** One narrator record card (rijāl or person): name + tradition + meta. */
export function NarratorCard({ item }: { item: NarratorItem }) {
  const sub = joinDots(item.kunya, item.nisba);
  return (
    <Card variant="flat" pad="md">
      <Stack gap="xs">
        <Inline gap="sm" align="center" justify="between">
          <Heading level={4} font="arabic" dir="rtl">
            {item.full_name}
          </Heading>
          {item.tradition ? <Badge>{item.tradition}</Badge> : null}
        </Inline>
        {sub ? (
          <Text size="sm" tone="muted" font="arabic" dir="rtl">
            {sub}
          </Text>
        ) : null}
        {isPerson(item) ? <PersonMeta entry={item} /> : <RijalMeta entry={item} />}
      </Stack>
    </Card>
  );
}
