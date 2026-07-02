import { useMemo } from 'react';
import { Spinner, Text } from '../../lib/design-system';
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

/** The landing page is the day's reading, not a brochure: the verse first,
    then the hadith beside the almanac rail (Hijri calendar + chronicles).
    Every surface opens the reader on click. */
export function HomeScreen({ onOpenReader }: HomeScreenProps) {
  const { data, error, loading } = useAsync<Daily>(() => getDaily(), []);
  const today = useMemo(() => hijriToday(), []);

  if (loading) return <Spinner label="Preparing today’s reading" />;
  if (error || !data) {
    return (
      <Text as="p" size="sm" tone="danger">
        Could not load today’s reading{error ? `: ${error.message}` : ''}.
      </Text>
    );
  }

  return (
    <div className="home">
      <header className="home-date" aria-label="Today">
        <span className="home-date__hijri" dir="rtl">
          {today.day} {today.monthAr} {today.year}
        </span>
        <span className="home-date__sep" aria-hidden="true">
          ·
        </span>
        <span className="home-date__greg">
          {today.weekdayEn} {today.gregorian}
        </span>
      </header>

      <VerseOfDay verse={data.verse} onOpenReader={onOpenReader} />

      <div className="home-band">
        <HadithOfDay hadith={data.hadith} onOpenReader={onOpenReader} />
        <Almanac today={today} />
      </div>
    </div>
  );
}
