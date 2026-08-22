import { Eyebrow } from '../../lib/design-system';
import { eventForDay } from '../../lib/almanac';
import { hijriMonthName } from '../../lib/hijri';
import type { HijriToday } from '../../lib/hijri';
import type { Almanac } from '../../lib/types';
import './Band.css';
import './ChroniclesBand.css';

export interface ChroniclesBandProps {
  almanac: Almanac;
  today: HijriToday;
}

/** The chronicles as a full-width band beneath the daily spread and before the
    book of the day: today's event, exact-matched to the Hijri day when one
    exists, otherwise a rotating pick from the table. */
export function ChroniclesBand({ almanac, today }: ChroniclesBandProps) {
  const { event, onThisDay } = eventForDay(almanac, today.month, today.day);
  return (
    <article className="band chband" aria-label="Today in history">
      <header className="chband__head">
        <Eyebrow>
          {onThisDay ? 'On this day · حدث في مثل هذا اليوم' : 'From the chronicles · من التاريخ'}
        </Eyebrow>
      </header>
      <div className="chband__body">
        <div className="chband__lockup">
          <p className="chband__when">
            {event.day} {hijriMonthName(event.month)} ·{' '}
            {event.year_ah > 0 ? `${event.year_ah} AH` : 'before the hijra'}
          </p>
          <h3 className="chband__title">{event.en}</h3>
        </div>
        <p className="chband__detail">{event.detail}</p>
      </div>
    </article>
  );
}
