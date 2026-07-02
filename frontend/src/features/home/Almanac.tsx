import { Eyebrow, Text } from '../../lib/design-system';
import { eventForDay, observancesForMonth } from '../../lib/almanac';
import type { HijriToday } from '../../lib/hijri';
import './Almanac.css';

export interface AlmanacProps {
  today: HijriToday;
}

/** The landing page's right rail: today's Hijri date with the month's
    observances, and an event from the chronicles keyed to the same day. */
export function Almanac({ today }: AlmanacProps) {
  return (
    <div className="almanac">
      <HijriCard today={today} />
      <HistoryCard today={today} />
    </div>
  );
}

function HijriCard({ today }: { today: HijriToday }) {
  const month = observancesForMonth(today.month);
  return (
    <article className="almanac__card" aria-label="Hijri calendar">
      <Eyebrow className="almanac__eyebrow">The calendar · التقويم</Eyebrow>
      <p className="almanac__today">
        <span className="almanac__today-day">{today.day}</span>
        <span className="almanac__today-month" dir="rtl">
          {today.monthAr}
        </span>
        <span className="almanac__today-year">{today.year} AH</span>
      </p>
      <Text as="p" size="xs" tone="faint" className="almanac__gregorian">
        {today.weekdayEn} · {today.gregorian}
      </Text>
      {month.length > 0 ? (
        <ul className="almanac__month" aria-label={`Observances in ${today.monthEn}`}>
          {month.map((o) => (
            <li
              key={`${o.month}-${o.day}-${o.en}`}
              className={
                o.day === today.day
                  ? 'almanac__row almanac__row--today'
                  : o.day < today.day
                    ? 'almanac__row almanac__row--past'
                    : 'almanac__row'
              }
            >
              <span className={`almanac__dot almanac__dot--${o.kind}`} aria-hidden="true" />
              <span className="almanac__row-day">{o.day}</span>
              <span className="almanac__row-body">
                <span className="almanac__row-en">{o.en}</span>
                <span className="almanac__row-ar" dir="rtl">
                  {o.ar}
                </span>
              </span>
              {o.day === today.day ? <span className="almanac__row-tag">today</span> : null}
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

function HistoryCard({ today }: { today: HijriToday }) {
  const { event, onThisDay } = eventForDay(today.month, today.day);
  return (
    <article className="almanac__card" aria-label="Today in history">
      <Eyebrow className="almanac__eyebrow">
        {onThisDay ? 'On this day · حدث في مثل هذا اليوم' : 'From the chronicles · من التاريخ'}
      </Eyebrow>
      <p className="almanac__event-when">
        {event.day} {monthName(event.month)} · {event.yearAh > 0 ? `${event.yearAh} AH` : 'before the hijra'}
      </p>
      <h3 className="almanac__event-title">{event.en}</h3>
      <Text as="p" size="sm" tone="muted" className="almanac__event-detail">
        {event.detail}
      </Text>
    </article>
  );
}

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
