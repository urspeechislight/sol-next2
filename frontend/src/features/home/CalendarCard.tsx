import { Eyebrow, Text } from '../../lib/design-system';
import { observancesForMonth } from '../../lib/almanac';
import type { HijriToday } from '../../lib/hijri';
import type { Almanac } from '../../lib/types';
import './CalendarCard.css';

export interface CalendarCardProps {
  almanac: Almanac;
  today: HijriToday;
}

/** The Hijri calendar as the folio's bottom-right card, filling the leaf's
    lower half: today's date over the month's observances, with today marked
    typographically (accent numeral + tag), never with a highlight bubble. */
export function CalendarCard({ almanac, today }: CalendarCardProps) {
  const month = observancesForMonth(almanac, today.month);
  return (
    <article className="calcard" aria-label="Hijri calendar">
      <Eyebrow className="calcard__eyebrow">The calendar · التقويم</Eyebrow>
      <p className="calcard__today">
        <span className="calcard__today-day">{today.day}</span>
        <span className="calcard__today-month" dir="rtl">
          {today.monthAr}
        </span>
        <span className="calcard__today-year">{today.year} AH</span>
      </p>
      <Text as="p" size="xs" tone="faint" className="calcard__gregorian">
        {today.weekdayEn} · {today.gregorian}
      </Text>
      {month.length > 0 ? (
        <ul className="calcard__month" aria-label={`Observances in ${today.monthEn}`}>
          {month.map((o) => (
            <li
              key={`${o.month}-${o.day}-${o.en}`}
              className={
                o.day === today.day
                  ? 'calcard__row calcard__row--today'
                  : o.day < today.day
                    ? 'calcard__row calcard__row--past'
                    : 'calcard__row'
              }
            >
              <span className={`calcard__dot calcard__dot--${o.kind}`} aria-hidden="true" />
              <span className="calcard__row-day">{o.day}</span>
              <span className="calcard__row-body">
                <span className="calcard__row-en">{o.en}</span>
                <span className="calcard__row-ar" dir="rtl">
                  {o.ar}
                </span>
              </span>
              {o.day === today.day ? <span className="calcard__row-tag">today</span> : null}
            </li>
          ))}
        </ul>
      ) : (
        <Text as="p" size="sm" tone="faint">
          No major observances this month.
        </Text>
      )}
    </article>
  );
}
