// PersonDrawer.tsx: the expandable detail panel under a person card. Enumerates
// the full teacher/student lists (fetched on demand), the source works the
// person is recorded in, every reliability grade, and the biography.
import { Stack, Text } from '../../lib/design-system';
import { getPersonEdges } from '../../lib/api/client';
import type { PersonEntry } from '../../lib/types';
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

export function PersonDrawer({ entry }: { entry: PersonEntry }) {
  const edges = useAsync(() => getPersonEdges(entry.person_id), [entry.person_id]);
  const all = edges.data ?? [];
  const teachers = all.filter((e) => e.relation === 'teacher');
  const students = all.filter((e) => e.relation === 'student');
  const names = (list: typeof all) => list.map((e) => e.name).join(' · ');
  return (
    <Stack gap="sm">
      {edges.loading ? (
        <Text size="xs" tone="faint">
          Loading detail…
        </Text>
      ) : null}
      <Section label={`Teachers (${teachers.length})`} value={names(teachers)} />
      <Section label={`Students (${students.length})`} value={names(students)} />
      <Section label="Recorded in" value={entry.source_books.replace(/ \| /g, ' · ')} />
      <Section label="Reliability gradings" value={entry.reliability.join(' · ')} />
      {entry.bio ? <Section label="Biography" value={entry.bio} /> : null}
    </Stack>
  );
}
