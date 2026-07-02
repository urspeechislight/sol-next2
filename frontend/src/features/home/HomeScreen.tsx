import { useMemo } from 'react';
import { PageGlow, Spinner, Text } from '../../lib/design-system';
import { getDaily } from '../../lib/api/client';
import { hijriToday } from '../../lib/hijri';
import type { Daily } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { Almanac } from './Almanac';
import { HadithOfDay } from './HadithOfDay';
import { VerseOfDay } from './VerseOfDay';
import './HomeScreen.css';

export interface HomeScreenProps {
  onOpenReader: (urn: string, page?: number) => void;
}

/** The landing page is the day's reading over one page-wide glow: verse and
    hadith side by side, history and calendar beneath them, every card a
    translucent surface the illumination reads through. */
export function HomeScreen({ onOpenReader }: HomeScreenProps) {
  const daily = useAsync<Daily>(() => getDaily(), []);
  const today = useMemo(() => hijriToday(), []);

  return (
    <div className="home2">
      <PageGlow />
      <section className="home2__daily" aria-label="Today's reading">
        <header className="home2__daily-head">
          <h2 className="home2__daily-title">
            <em>Today’s</em> reading
          </h2>
          <span className="home2__daily-date">
            <span className="home2__daily-hijri" dir="rtl">
              {today.day} {today.monthAr} {today.year}
            </span>
            <span className="home2__daily-sep" aria-hidden="true">
              ·
            </span>
            {today.weekdayEn} {today.gregorian}
          </span>
        </header>
        {daily.loading ? <Spinner label="Preparing today’s reading" /> : null}
        {daily.error ? (
          <Text as="p" size="sm" tone="danger">
            Could not load today’s reading: {daily.error.message}
          </Text>
        ) : null}
        {daily.data ? (
          <div className="home2__band">
            <VerseOfDay verse={daily.data.verse} onOpenReader={onOpenReader} />
            <HadithOfDay hadith={daily.data.hadith} onOpenReader={onOpenReader} />
            <Almanac today={today} />
          </div>
        ) : null}
      </section>
    </div>
  );
}
