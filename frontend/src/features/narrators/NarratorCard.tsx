// NarratorCard.tsx:the one narrator-record card, shared by the Graph browser
// and the narrator search scope. Renders a rijāl OR canonical entry as
// name + tradition + a kind-specific meta row, so the two surfaces stay
// identical instead of each hand-rolling a near-copy.
import { Badge, Card, Heading, Inline, Stack, Text } from '../../lib/design-system';
import type { CanonicalEntry, RijalEntry } from '../../lib/types';
import { joinDots } from '../../lib/utils';
import { confidenceBadge, confidenceLabel, reliabilityBadge } from '../../lib/variants';

export type NarratorItem = RijalEntry | CanonicalEntry;

/** True when a narrator item is a merged canonical profile (vs a rijāl entry). */
export function isCanonical(item: NarratorItem): item is CanonicalEntry {
  return 'canonical_id' in item;
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

function CanonicalMeta({ entry }: { entry: CanonicalEntry }) {
  return (
    <Inline gap="xs" align="center">
      <Badge variant={confidenceBadge(entry.merge_confidence)}>
        {confidenceLabel(entry.merge_confidence)}
      </Badge>
      <Text size="xs" tone="faint" font="mono">
        {entry.entry_count} entries · {entry.source_count} sources · {entry.teacher_count} teachers
      </Text>
    </Inline>
  );
}

/** One narrator record card (rijāl or canonical): name + tradition + meta. */
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
        {isCanonical(item) ? <CanonicalMeta entry={item} /> : <RijalMeta entry={item} />}
      </Stack>
    </Card>
  );
}
