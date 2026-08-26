// NarratorDrawer.tsx:the expandable detail panel under a narrator card. Lays
// out the name variants grouped by role (primary / variant / kunya / nisba),
// the recorded dates, every reliability grade grouped by the critic who
// issued it (term + tier + source), the ALID stances, and the biographical
// tarjama snippets — plus the affordance that opens the ego graph view.
import { Card, Inline, Stack, Text, UnstyledButton } from '../../lib/design-system';
import { EgoGraph } from '../graph/EgoGraph';
import { ErrorText } from '../../lib/DataView';
import type { AsyncLike } from '../../lib/DataView';
import type { NarratorAlias, NarratorDetail, NarratorGrade } from '../../lib/types';
import { joinDots } from '../../lib/utils';
import {
  categoryLabel,
  gradeLabel,
  residenceLabel,
  stancePredicateLabel,
  stanceValueLabel,
  traditionLabel,
} from './labels';
import './NarratorDrawer.css';

const ROLE_ORDER = ['primary', 'variant', 'kunya', 'nisba'] as const;

const ROLE_LABEL: Record<string, string> = {
  primary: 'Primary names',
  variant: 'Recorded variants',
  kunya: 'Kunya (teknonym, Abū / Umm …)',
  nisba: 'Nisba (lineage or place)',
};

function Fact({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div>
      <Text size="xs" tone="muted" weight="semibold">
        {label}
      </Text>
      <Text size="sm" tone="muted">
        {value}
      </Text>
    </div>
  );
}

/** One role's aliases as compact chips: the Arabic spelling with its source
    work beneath, wrapped in a flowing row so a long variant list stays dense
    instead of one tall column. */
function AliasGroup({ role, aliases }: { role: string; aliases: NarratorAlias[] }) {
  if (aliases.length === 0) return null;
  return (
    <div>
      <Text size="xs" tone="muted" weight="semibold">
        {`${ROLE_LABEL[role] ?? role} (${aliases.length})`}
      </Text>
      <Inline gap="xs" wrap>
        {aliases.map((a, i) => (
          <Card key={`${a.name_ar}-${i}`} variant="flat" pad="none" className="narrator-alias">
            <Stack gap="none">
              <Text size="xs" font="arabic" dir="rtl">
                {a.name_ar}
              </Text>
              {a.source_label ? (
                <Text size="xs" tone="faint">
                  {a.source_label}
                </Text>
              ) : null}
            </Stack>
          </Card>
        ))}
      </Inline>
    </div>
  );
}

function AliasGroups({ aliases }: { aliases: NarratorAlias[] }) {
  const byRole = new Map<string, NarratorAlias[]>();
  for (const alias of aliases) {
    const bucket = byRole.get(alias.name_role) ?? [];
    bucket.push(alias);
    byRole.set(alias.name_role, bucket);
  }
  const roles: string[] = ROLE_ORDER.filter((role) => byRole.has(role));
  for (const role of byRole.keys()) {
    if (!roles.includes(role)) roles.push(role);
  }
  if (roles.length === 0) return null;
  return (
    <Stack gap="sm">
      {roles.map((role) => (
        <AliasGroup key={role} role={role} aliases={byRole.get(role) ?? []} />
      ))}
    </Stack>
  );
}

/** One grade row: the Arabic verdict, its tier's English label, and the
    provenance (source work label, plus the book id + locator when recorded). */
function GradeRow({ grade }: { grade: NarratorGrade }) {
  const locator = joinDots(
    grade.source_label,
    grade.source_book
      ? `${grade.source_book}${grade.source_locator ? ` · ${grade.source_locator}` : ''}`
      : '',
  );
  return (
    <div>
      <Inline gap="xs" align="center">
        <Text size="sm" font="arabic" dir="rtl">
          {grade.term}
        </Text>
        <Text size="xs" tone="muted">
          {gradeLabel(grade.tier || grade.term)}
        </Text>
      </Inline>
      {locator ? (
        <Text size="xs" tone="faint">
          {locator}
        </Text>
      ) : null}
    </div>
  );
}

/** The gradings grouped by the critic who issued them: one labelled group
    per evaluator, each row a verdict + tier + provenance. */
function Gradings({ grades }: { grades: NarratorGrade[] }) {
  if (grades.length === 0) return null;
  const byEvaluator = new Map<string, NarratorGrade[]>();
  for (const grade of grades) {
    const key = grade.evaluator || 'Unattributed';
    const bucket = byEvaluator.get(key) ?? [];
    bucket.push(grade);
    byEvaluator.set(key, bucket);
  }
  return (
    <Stack gap="sm">
      {[...byEvaluator.entries()].map(([evaluator, group]) => (
        <div key={evaluator}>
          <Text size="xs" tone="muted" weight="semibold">
            {`${evaluator} (${group.length})`}
          </Text>
          <Stack gap="xs">
            {group.map((g, i) => (
              <GradeRow key={`${g.term}-${i}`} grade={g} />
            ))}
          </Stack>
        </div>
      ))}
    </Stack>
  );
}

function Stances({ stances }: { stances: NarratorDetail['stances'] }) {
  if (stances.length === 0) return null;
  return (
    <Stack gap="xs">
      {stances.map((s, i) => (
        <div key={`${s.predicate ?? ''}-${i}`}>
          <Text size="xs" tone="muted" weight="semibold">
            {stancePredicateLabel(s.predicate ?? '')}
          </Text>
          <Text size="sm" tone="muted">
            {stanceValueLabel(s.value_text ?? '')}
          </Text>
        </div>
      ))}
    </Stack>
  );
}

function Tarjama({ blocks }: { blocks: string[] }) {
  if (blocks.length === 0) return null;
  return (
    <Stack gap="xs">
      {blocks.map((text, i) => (
        <Text
          key={i}
          as="p"
          size="sm"
          tone="muted"
          font="arabic"
          dir="rtl"
          className="narrator-tarjama"
        >
          {text}
        </Text>
      ))}
    </Stack>
  );
}

export function NarratorDrawer({
  entryId,
  detail,
  graphOpen,
  onOpenGraph,
}: {
  entryId: number;
  detail: AsyncLike<NarratorDetail | null>;
  graphOpen: boolean;
  onOpenGraph: () => void;
}) {
  return (
    <Stack gap="sm">
      {detail.loading ? (
        <Text size="xs" tone="faint">
          Loading detail…
        </Text>
      ) : null}
      {detail.error ? (
        <ErrorText>{`Could not load the detail: ${detail.error.message}`}</ErrorText>
      ) : null}
      {detail.data ? (
        <>
          <Fact label="Attested in" value={traditionLabel(detail.data.tradition)} />
          <Fact
            label="Dates"
            value={joinDots(
              detail.data.birth_year_ah != null ? `b. ${detail.data.birth_year_ah} AH` : '',
              detail.data.death_year_ah != null ? `d. ${detail.data.death_year_ah} AH` : '',
              detail.data.death_year_ce,
            )}
          />
          <Fact label="Entry class" value={categoryLabel(detail.data.category)} />
          <Fact
            label="Places & generation"
            value={joinDots(
              detail.data.tabaqa ? detail.data.tabaqa : '',
              residenceLabel(
                joinDots(detail.data.living_city, detail.data.death_place),
              ),
            )}
          />
          <AliasGroups aliases={detail.data.aliases} />
          <Gradings grades={detail.data.grades} />
          <Stances stances={detail.data.stances} />
          <Tarjama blocks={detail.data.tarjama} />
        </>
      ) : null}
      <UnstyledButton onClick={onOpenGraph} ariaExpanded={graphOpen}>
        <Text size="xs" tone="accent">
          {graphOpen ? 'Hide transmission graph' : 'View transmission graph'}
        </Text>
      </UnstyledButton>
      {/* entryId keys the graph mount so re-opening another narrator's graph
          starts from that narrator, not a stale recentred root. */}
      {graphOpen ? <EgoGraph key={entryId} entryId={entryId} /> : null}
    </Stack>
  );
}
