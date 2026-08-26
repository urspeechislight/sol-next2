// NarratorCard.tsx:the one narrator-record card, shared by the Graph browser
// and the narrator search scope. Renders the registry entry as primary name
// (Arabic + Latin) + tradition + dates + relation counts, and expands into a
// detail drawer (aliases by role, gradings by evaluator, stances, tarjama)
// whose fetch also derives the top-grade chip shown in the meta row.
import { useState } from 'react';

import { Badge, Card, Heading, Inline, Stack, Text, UnstyledButton } from '../../lib/design-system';
import { getNarratorEntry } from '../../lib/api/client';
import type { NarratorDetail, NarratorEntry } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { deathLabel, joinDots } from '../../lib/utils';
import { reliabilityBadge, topTier } from '../../lib/variants';
import { gradeLabel, traditionLabel } from './labels';
import { NarratorDrawer } from './NarratorDrawer';

/** One narrator record card: name + tradition + meta + expandable detail. */
export function NarratorCard({ item }: { item: NarratorEntry }) {
  const [open, setOpen] = useState(false);
  const [graph, setGraph] = useState(false);
  // The detail is fetched only when the drawer opens (null while closed);
  // the top-grade chip in the meta row reads from this same fetch — the
  // NarratorEntry list row carries no grade, so the chip appears with the
  // detail, never fabricated from the list shape.
  const detail = useAsync<NarratorDetail | null>(
    () => (open ? getNarratorEntry(item.id) : Promise.resolve(null)),
    [open, item.id],
  );
  const tier = topTier((detail.data?.grades ?? []).map((g) => g.tier));
  const sub = joinDots(item.kunya, item.nisba);
  const meta = joinDots(
    deathLabel(item.death_year_ah),
    item.death_year_ce,
    `${item.teacher_count} teachers · ${item.student_count} students`,
  );
  return (
    <Card variant="flat" pad="md">
      <Stack gap="xs">
        <Inline gap="sm" align="start" justify="between">
          <Stack gap="xs">
            {item.primary_name_en ? (
              <Text size="sm" weight="semibold">
                {item.primary_name_en}
              </Text>
            ) : null}
            <Heading level={4} font="arabic" dir="rtl">
              {item.primary_name_ar}
            </Heading>
          </Stack>
          {item.tradition ? <Badge>{traditionLabel(item.tradition)}</Badge> : null}
        </Inline>
        {sub ? (
          <Text size="sm" tone="muted" font="arabic" dir="rtl">
            {sub}
          </Text>
        ) : null}
        <Inline gap="xs" align="center">
          {tier ? <Badge variant={reliabilityBadge(tier)}>{gradeLabel(tier)}</Badge> : null}
          <Text size="xs" tone="faint" font="mono">
            {meta}
          </Text>
        </Inline>
        <UnstyledButton onClick={() => setOpen((value) => !value)} ariaExpanded={open}>
          <Text size="xs" tone="accent">
            {open ? 'Hide detail' : 'Show names, gradings, stances, tarjama'}
          </Text>
        </UnstyledButton>
        {open ? (
          <NarratorDrawer
            entryId={item.id}
            detail={detail}
            graphOpen={graph}
            onOpenGraph={() => setGraph((value) => !value)}
          />
        ) : null}
      </Stack>
    </Card>
  );
}
