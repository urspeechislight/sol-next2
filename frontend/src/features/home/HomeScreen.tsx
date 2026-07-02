import { useMemo, useRef } from 'react';
import { Spinner, Text } from '../../lib/design-system';
import { getDaily } from '../../lib/api/client';
import { hijriToday } from '../../lib/hijri';
import type { Daily } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { useDomains } from '../../lib/useDomains';
import { Almanac } from './Almanac';
import { DomainDrawers } from './DomainDrawers';
import { HadithOfDay } from './HadithOfDay';
import { HomeHero } from './HomeHero';
import { Cornerpiece, HomeSky } from './HomeSky';
import { VerseOfDay } from './VerseOfDay';
import './HomeScreen.css';

export interface HomeScreenProps {
  onOpenReader: (urn: string, page?: number) => void;
  onOpenCategory: (slug: string) => void;
  onOpenDomain: (id: string) => void;
}

/** The landing page in two registers: the illuminated frontispiece (the glow
    canvas, hero copy, the astrolabe of domains, the drawer cabinet) and the
    day's reading below it — verse, hadith and almanac as one compact
    three-panel band. */
export function HomeScreen({ onOpenReader, onOpenCategory, onOpenDomain }: HomeScreenProps) {
  const domains = useDomains();
  const daily = useAsync<Daily>(() => getDaily(), []);
  const today = useMemo(() => hijriToday(), []);
  const dailyRef = useRef<HTMLElement | null>(null);
  const scrollToDaily = () => dailyRef.current?.scrollIntoView({ behavior: 'smooth' });

  return (
    <div className="home2">
      <div className="home2__plate">
        <HomeSky />
        <Cornerpiece pos="tl" />
        <Cornerpiece pos="tr" />
        <Cornerpiece pos="bl" />
        <Cornerpiece pos="br" />
        <HomeHero
          domains={domains.data ?? []}
          onOpenDomain={onOpenDomain}
          onBrowse={() => onOpenDomain('')}
          onToday={scrollToDaily}
        />
        <div className="home2__rule" aria-hidden="true" />
        {domains.error ? (
          <Text as="p" size="sm" tone="danger" className="home2__domains-error">
            Could not load the domains: {domains.error.message}
          </Text>
        ) : (
          <DomainDrawers
            domains={domains.data ?? []}
            onOpenCategory={onOpenCategory}
            onOpenDomain={onOpenDomain}
          />
        )}
      </div>

      <section className="home2__daily" ref={dailyRef} aria-label="Today's reading">
        <header className="home2__daily-head">
          <span className="home2__daily-mark">§ II</span>
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
