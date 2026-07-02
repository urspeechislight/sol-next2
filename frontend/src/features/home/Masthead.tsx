import { Text } from '../../lib/design-system';
import type { HijriToday } from '../../lib/hijri';
import { useDomains } from '../../lib/useDomains';
import './Masthead.css';

const BASMALA = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ';

interface Counts {
  works: number;
  volumes: number;
  domains: number;
}

function countsOf(domains: ReturnType<typeof useDomains>['data']): Counts | null {
  if (!domains) return null;
  return {
    works: domains.reduce((n, d) => n + d.categories.reduce((m, c) => m + c.count, 0), 0),
    volumes: domains.reduce((n, d) => n + d.categories.reduce((m, c) => m + c.volume_count, 0), 0),
    domains: domains.length,
  };
}

export interface MastheadProps {
  today: HijriToday;
}

/** The masthead beneath the ʿunwān: the basmala at display scale, the
    library's one-line identity, its true extent summed live from the
    taxonomy, and the Hijri dateline. The Arabic leads; English subordinates. */
export function Masthead({ today }: MastheadProps) {
  const domains = useDomains();
  const counts = countsOf(domains.data);
  return (
    <header className="masthead">
      <p className="masthead__basmala" dir="rtl">
        {BASMALA}
      </p>
      <h1 className="masthead__title">A reader for the Islamic textual tradition</h1>
      {counts ? (
        <p className="masthead__scale">
          {counts.works.toLocaleString('en')} works · {counts.volumes.toLocaleString('en')} volumes
          · {counts.domains} domains
        </p>
      ) : null}
      {domains.error ? (
        <Text as="p" size="sm" tone="danger">
          Could not load the catalogue: {domains.error.message}
        </Text>
      ) : null}
      <p className="masthead__date">
        <span className="masthead__date-ar" dir="rtl">
          {today.day} {today.monthAr} {today.year}
        </span>
        <span className="masthead__date-sep" aria-hidden="true">
          ·
        </span>
        {today.weekdayEn} {today.gregorian}
      </p>
    </header>
  );
}
