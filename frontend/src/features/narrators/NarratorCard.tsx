// NarratorCard.tsx:the one narrator-record card, shared by the Graph browser
// and the narrator search scope. Renders a rijāl OR enriched person entry as
// name + tradition + a kind-specific meta row; a person card also expands into
// a detail drawer (teachers, students, sources, bio).
import { useState } from 'react';

import { Badge, Card, Heading, Inline, Stack, Text, UnstyledButton } from '../../lib/design-system';
import type { PersonEntry, RijalEntry } from '../../lib/types';
import { joinDots } from '../../lib/utils';
import { reliabilityBadge } from '../../lib/variants';
import { PersonDrawer } from './PersonDrawer';

export type NarratorItem = RijalEntry | PersonEntry;

/** True when a narrator item is an enriched person record (vs a raw rijāl entry). */
export function isPerson(item: NarratorItem): item is PersonEntry {
  return 'person_id' in item;
}

/** Human label for the corpus a narrator is attested in. */
function traditionLabel(tradition: string): string {
  if (tradition === 'both') return 'Sunnī + Shīʿī';
  if (tradition === 'sunni') return 'Sunnī';
  if (tradition === 'shia') return 'Shīʿī';
  if (tradition === 'history') return 'History';
  return tradition;
}

/** Human label for a derived narrator generation. */
function generationLabel(generation: string): string {
  if (generation === 'companion') return 'Ṣaḥābī';
  if (generation === 'successor') return 'Tābiʿī';
  if (generation === 'successor_of_successors') return 'Tābiʿ al-tābiʿīn';
  return '';
}

const RESIDENCE_EN: Record<string, string> = {
  كوفي: 'Kufan',
  مكي: 'Meccan',
  مدني: 'Medinan',
  بصري: 'Basran',
  بغدادي: 'Baghdadi',
  دمشقي: 'Damascene',
  مصري: 'Egyptian',
  شامي: 'Syrian',
  يمني: 'Yemeni',
  رازي: 'of Rayy',
  همداني: 'Hamadhani',
  قمي: 'Qummi',
  خراساني: 'Khurasani',
  واسطي: 'Wasiti',
  أصبهاني: 'Isfahani',
  اصبهاني: 'Isfahani',
  نيسابوري: 'Nishapuri',
  حمصي: 'of Homs',
  قزويني: 'of Qazwin',
  جرجاني: 'of Gurgan',
  مروزي: 'of Merv',
  بلخي: 'Balkhi',
};

/** Render the residence nisbas in English (Kufan, Medinan, …), passing through the rest. */
function residenceLabel(places: string): string {
  return places
    .split(' | ')
    .map((place) => RESIDENCE_EN[place.trim()] ?? place.trim())
    .join(', ');
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
      {entry.generation ? <Badge variant="success">{generationLabel(entry.generation)}</Badge> : null}
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

/** One narrator record card (rijāl or person): name + tradition + meta + detail. */
export function NarratorCard({ item }: { item: NarratorItem }) {
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
              {open ? 'Hide detail' : 'Show teachers, students, sources, bio'}
            </Text>
          </UnstyledButton>
        ) : null}
        {person && open ? <PersonDrawer entry={item} /> : null}
      </Stack>
    </Card>
  );
}
