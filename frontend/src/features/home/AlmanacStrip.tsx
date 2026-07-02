import { Text } from '../../lib/design-system';
import { eventForDay, observancesForMonth } from '../../lib/almanac';
import { getAlmanac } from '../../lib/api/client';
import type { HijriToday } from '../../lib/hijri';
import type { Almanac, Observance } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import './AlmanacStrip.css';

const HIJRI_MONTHS_EN = [
  'Muḥarram',
  'Ṣafar',
  'Rabīʿ al-Awwal',
  'Rabīʿ al-Thānī',
  'Jumādā al-Ūlā',
  'Jumādā al-Ākhira',
  'Rajab',
  'Shaʿbān',
  'Ramaḍān',
  'Shawwāl',
  'Dhū al-Qaʿda',
  'Dhū al-Ḥijja',
] as const;

function monthName(month: number): string {
  return HIJRI_MONTHS_EN[month - 1] ?? String(month);
}

function nextObservance(almanac: Almanac, today: HijriToday): Observance | null {
  return observancesForMonth(almanac, today.month).find((o) => o.day >= today.day) ?? null;
}

export interface AlmanacStripProps {
  today: HijriToday;
}

/** The almanac as one quiet line under the daily spread: the chronicle entry
    for today (exact when the date matches, a rotating pick otherwise) and the
    month's next observance. Flavor, not a task — one line of hierarchy. */
export function AlmanacStrip({ today }: AlmanacStripProps) {
  const almanac = useAsync<Almanac>(() => getAlmanac(), []);
  if (almanac.loading) return null;
  if (almanac.error) {
    return (
      <Text as="p" size="sm" tone="danger">
        Could not load the almanac: {almanac.error.message}
      </Text>
    );
  }
  if (!almanac.data) return null;

  const { event, onThisDay } = eventForDay(almanac.data, today.month, today.day);
  const next = nextObservance(almanac.data, today);
  return (
    <aside className="alstrip" aria-label="Almanac">
      <span className="alstrip__label">{onThisDay ? 'On this day' : 'From the chronicles'}</span>
      <span className="alstrip__event" title={event.detail}>
        {event.en}
        <span className="alstrip__when">
          {' '}
          · {event.day} {monthName(event.month)}
          {event.year_ah > 0 ? ` ${event.year_ah} AH` : ', before the hijra'}
        </span>
      </span>
      <span className="alstrip__next">
        {next
          ? `Next: ${next.en} · ${next.day} ${today.monthEn}`
          : `No observances left in ${today.monthEn}`}
      </span>
    </aside>
  );
}
