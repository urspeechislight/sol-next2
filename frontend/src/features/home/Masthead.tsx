import { DataView } from '../../lib/DataView';
import type { HijriToday } from '../../lib/hijri';
import { corpusTotals } from '../../lib/taxonomy';
import { useDomains } from '../../lib/useDomains';
import { countLabel } from '../../lib/utils';
import './Masthead.css';

const BASMALA = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ';

export interface MastheadProps {
  today: HijriToday;
}

/** The masthead beneath the ʿunwān: the basmala at display scale, the
    library's one-line identity, its true extent summed live from the
    taxonomy, and the Hijri dateline. The Arabic leads; English subordinates. */
export function Masthead({ today }: MastheadProps) {
  const domains = useDomains();
  return (
    <header className="masthead">
      <p className="masthead__basmala" dir="rtl">
        {BASMALA}
      </p>
      <h1 className="masthead__title">A reader for the Islamic textual tradition</h1>
      <DataView
        result={domains}
        renderLoading={() => null}
        errorText="Could not load the catalogue"
      >
        {(data) => {
          const counts = corpusTotals(data);
          return (
            <p className="masthead__scale">
              {countLabel(counts.works, 'work')} · {countLabel(counts.volumes, 'volume')} ·{' '}
              {countLabel(counts.domains, 'domain')}
            </p>
          );
        }}
      </DataView>
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
