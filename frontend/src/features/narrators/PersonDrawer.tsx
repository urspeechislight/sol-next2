// PersonDrawer.tsx: the expandable detail panel under a person card. Lays out the
// labelled identity (kunya, nisba, tradition, Ahl al-Bayt stance, generation), the
// full teacher/student lists, every reliability grade re-validated against its cited
// source page (each a reader deep-link), the source works, and the biography.
import { Link, Stack, Text } from '../../lib/design-system';
import { getPersonEdges, getPersonGrades } from '../../lib/api/client';
import type { PersonEdge, PersonEntry, PersonGrade } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { generationLabel, residenceLabel, stanceHelp, stanceLabel, traditionLabel } from './labels';

function Section({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div>
      <Text size="xs" tone="muted" weight="semibold">
        {label}
      </Text>
      <Text size="sm" tone="muted" font="arabic" dir="rtl">
        {value}
      </Text>
    </div>
  );
}

/** One labelled identity fact; the label names the concept so a reader learns the term. */
function Fact({
  label,
  value,
  help,
  arabic,
}: {
  label: string;
  value: string;
  help?: string;
  arabic?: boolean;
}) {
  if (!value) return null;
  return (
    <div>
      <Text size="xs" tone="muted" weight="semibold">
        {label}
      </Text>
      <Text
        size="sm"
        tone="muted"
        font={arabic ? 'arabic' : undefined}
        dir={arabic ? 'rtl' : undefined}
      >
        {value}
      </Text>
      {help ? (
        <Text size="xs" tone="faint">
          {help}
        </Text>
      ) : null}
    </div>
  );
}

/** A teacher/student relation list: one name per row, matching the grade list format. */
function NameList({ label, edges }: { label: string; edges: PersonEdge[] }) {
  if (edges.length === 0) return null;
  return (
    <div>
      <Text size="xs" tone="muted" weight="semibold">
        {label}
      </Text>
      <Stack gap="xs">
        {edges.map((e, i) => (
          <Text key={`${e.name}-${i}`} size="sm" tone="muted" font="arabic" dir="rtl">
            {e.name}
          </Text>
        ))}
      </Stack>
    </div>
  );
}

function GradeRow({ grade }: { grade: PersonGrade }) {
  const where = grade.page ? `${grade.book} · ص ${grade.page}` : grade.book;
  return (
    <div>
      <Link href={grade.link} variant="accent" dir="rtl">
        <Text size="sm" font="arabic" dir="rtl">
          {grade.evaluator}: {grade.term}
        </Text>
      </Link>
      <Text size="xs" tone="faint" font="arabic" dir="rtl">
        {where}
      </Text>
    </div>
  );
}

function Gradings({ grades }: { grades: PersonGrade[] }) {
  if (grades.length === 0) return null;
  return (
    <div>
      <Text size="xs" tone="muted" weight="semibold">
        {`Reliability gradings (${grades.length}): each links to its source page`}
      </Text>
      <Stack gap="xs">
        {grades.map((g, i) => (
          <GradeRow key={`${g.evaluator}-${g.page}-${g.term}-${i}`} grade={g} />
        ))}
      </Stack>
    </div>
  );
}

export function PersonDrawer({ entry }: { entry: PersonEntry }) {
  const edges = useAsync(() => getPersonEdges(entry.person_id), [entry.person_id]);
  const grades = useAsync(() => getPersonGrades(entry.person_id), [entry.person_id]);
  const all = edges.data ?? [];
  const teachers = all.filter((e) => e.relation === 'teacher');
  const students = all.filter((e) => e.relation === 'student');
  const stanceValue = entry.stance ? stanceLabel(entry.stance) : 'Not evaluated in the sources';
  const died = entry.death_year
    ? `${entry.death_year} AH${entry.death_conflict ? ' (sources differ)' : ''}`
    : '';
  return (
    <Stack gap="sm">
      {edges.loading || grades.loading ? (
        <Text size="xs" tone="faint">
          Loading detail…
        </Text>
      ) : null}
      <Fact label="Kunya (teknonym, Abū / Umm …)" value={entry.kunya} arabic />
      <Fact
        label="Nisba (lineage or place)"
        value={entry.nisba || 'Not recorded in his own entries'}
        arabic={Boolean(entry.nisba)}
      />
      <Fact label="Attested in" value={traditionLabel(entry.tradition)} />
      <Fact
        label="Ahl al-Bayt stance"
        value={stanceValue}
        help={entry.stance ? stanceHelp(entry.stance) : ''}
      />
      <Fact label="Generation (ṭabaqa)" value={generationLabel(entry.generation)} />
      <Fact label="Died" value={died} />
      <Fact label="Residence" value={entry.places ? residenceLabel(entry.places) : ''} />
      <NameList label={`Teachers (${teachers.length})`} edges={teachers} />
      <NameList label={`Students (${students.length})`} edges={students} />
      <Gradings grades={grades.data ?? []} />
      <Section label="Recorded in" value={entry.source_books.replace(/ \| /g, ' · ')} />
      {entry.bio ? <Section label="Biography" value={entry.bio} /> : null}
    </Stack>
  );
}
