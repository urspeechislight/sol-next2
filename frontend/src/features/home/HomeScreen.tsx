import { useMemo } from 'react';
import { PageGlow } from '../../lib/design-system';
import { DataView } from '../../lib/DataView';
import { getDaily } from '../../lib/api/client';
import { hijriToday } from '../../lib/hijri';
import type { Daily } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { Almanac } from './Almanac';
import { BookOfDay } from './BookOfDay';
import { FihristBand } from './FihristBand';
import { HadithOfDay } from './HadithOfDay';
import { Masthead } from './Masthead';
import { ResumeStrip } from './ResumeStrip';
import { Unwan } from './Unwan';
import { VerseOfDay } from './VerseOfDay';
import './HomeScreen.css';

export interface HomeScreenProps {
  onOpenReader: (urn: string, page?: number) => void;
}

/** The landing page as a manuscript folio. An illuminated ʿunwān and masthead
    open the page; a conditional resume strip re-enters the last book; the
    daily spread sets verse and hadith as equal columns either side of a
    center rule, with the book of the day as its own band beneath; the almanac
    sets today's chronicle beside the month's calendar; the fihrist of domains
    turns the corpus's scale into navigation; a colophon closes the folio the
    way a manuscript ends. */
export function HomeScreen({ onOpenReader }: HomeScreenProps) {
  const daily = useAsync<Daily>(() => getDaily(), []);
  const today = useMemo(() => hijriToday(), []);

  return (
    <div className="home3">
      <PageGlow />
      <div className="home3__inner">
        <Unwan />
        <Masthead today={today} />
        <ResumeStrip onOpenReader={onOpenReader} />
        <DataView
          result={daily}
          loadingLabel="Preparing today's reading"
          errorText="Could not load today's reading"
        >
          {(data) => (
            <>
              <section className="home3__folio" aria-label="Today's reading">
                <VerseOfDay verse={data.verse} onOpenReader={onOpenReader} />
                <HadithOfDay hadith={data.hadith} onOpenReader={onOpenReader} />
              </section>
              <BookOfDay pick={data.book} onOpenReader={onOpenReader} />
              <Almanac today={today} />
            </>
          )}
        </DataView>
        <FihristBand />
        <Colophon />
      </div>
    </div>
  );
}

/** The folio's close: a manuscript ends with a colophon, so the page does not
    trail off into bare ground. */
function Colophon() {
  return (
    <footer className="home3__colophon">
      <span className="home3__colophon-mark" aria-hidden="true">
        ✻
      </span>
      <p className="home3__colophon-line">
        A reading room for the classical Islamic library, set in Amiri, Scheherazade, and Newsreader
        on warm paper.
      </p>
    </footer>
  );
}
