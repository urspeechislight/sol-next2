import { Eyebrow, IndexRow } from '../../lib/design-system';
import { DataView } from '../../lib/DataView';
import { buildHash, EMPTY_ROUTE } from '../../lib/routes';
import { domainTotals } from '../../lib/taxonomy';
import type { Domain } from '../../lib/types';
import { useDomains } from '../../lib/useDomains';
import { countLabel } from '../../lib/utils';
import './FihristBand.css';

function domainHref(id: string): string {
  return buildHash({ ...EMPTY_ROUTE, view: 'library', dom: id });
}

function totalsLine(domain: Domain): string {
  const totals = domainTotals(domain);
  return `${countLabel(totals.works, 'work')} · ${countLabel(totals.volumes, 'vol')}`;
}

/** The fihrist: the library's own table of contents as the landing page's
    close. Seven domains typeset as contents rows (the shared IndexRow
    grammar), each a door into Browse pre-filtered to that domain. Scale
    becomes navigation, not statistics. */
export function FihristBand() {
  const domains = useDomains();
  return (
    <section className="fihrist" aria-labelledby="fihrist-title">
      <header className="fihrist__head">
        <Eyebrow>The fihrist · الفهرست</Eyebrow>
        <h2 id="fihrist-title" className="fihrist__title">
          Browse the library
        </h2>
      </header>
      <DataView
        result={domains}
        loadingLabel="Opening the catalogue"
        errorText="Could not load the catalogue"
      >
        {(data) => (
          <ol className="fihrist__list">
            {data.map((d) => (
              <li key={d.id} className="fihrist__item">
                <IndexRow
                  en={d.label}
                  ar={d.label_ar}
                  blurb={d.blurb}
                  meta={totalsLine(d)}
                  href={domainHref(d.id)}
                />
              </li>
            ))}
          </ol>
        )}
      </DataView>
    </section>
  );
}
