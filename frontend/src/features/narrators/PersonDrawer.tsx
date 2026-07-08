// PersonDrawer.tsx: the expandable detail panel under a person card. Enumerates
// the full teacher/student lists (fetched on demand), the source works the
// person is recorded in, every reliability grade re-validated against its cited
// source page (each a reader deep-link), and the biography.
import { Link, Stack, Text } from '../../lib/design-system';
import { getPersonEdges, getPersonGrades } from '../../lib/api/client';
import type { PersonEntry, PersonGrade } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';

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
  const names = (list: typeof all) => list.map((e) => e.name).join(' · ');
  return (
    <Stack gap="sm">
      {edges.loading || grades.loading ? (
        <Text size="xs" tone="faint">
          Loading detail…
        </Text>
      ) : null}
      <Section label={`Teachers (${teachers.length})`} value={names(teachers)} />
      <Section label={`Students (${students.length})`} value={names(students)} />
      <Section label="Recorded in" value={entry.source_books.replace(/ \| /g, ' · ')} />
      <Gradings grades={grades.data ?? []} />
      {entry.bio ? <Section label="Biography" value={entry.bio} /> : null}
    </Stack>
  );
}
