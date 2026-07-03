import { DataView } from '../../lib/DataView';
import { eventForDay, observancesForMonth } from '../../lib/almanac';
import { getAlmanac } from '../../lib/api/client';
import { hijriMonthName } from '../../lib/hijri';
import type { HijriToday } from '../../lib/hijri';
import type { Almanac, Observance } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import './AlmanacStrip.css';

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
  return (
    <DataView
      result={almanac}
      renderLoading={() => null}
      errorText="Could not load the almanac"
    >
      {(data) => {
        const { event, onThisDay } = eventForDay(data, today.month, today.day);
        const next = nextObservance(data, today);
        return (
          <aside className="alstrip" aria-label="Almanac">
            <span className="alstrip__label">
              {onThisDay ? 'On this day' : 'From the chronicles'}
            </span>
            <span className="alstrip__event" title={event.detail}>
              {event.en}
              <span className="alstrip__when">
                {' '}
                · {event.day} {hijriMonthName(event.month)}
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
      }}
    </DataView>
  );
}
