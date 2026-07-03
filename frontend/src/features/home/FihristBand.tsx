import { Eyebrow, IndexRow, Spinner, Text } from '../../lib/design-system';
import { buildHash, EMPTY_ROUTE } from '../../lib/routes';
import type { Domain } from '../../lib/types';
import { useDomains } from '../../lib/useDomains';
import './FihristBand.css';

function domainHref(id: string): string {
  return buildHash({ ...EMPTY_ROUTE, view: 'library', dom: id });
}

function totalsLine(domain: Domain): string {
  const works = domain.categories.reduce((n, c) => n + c.count, 0);
  const volumes = domain.categories.reduce((n, c) => n + c.volume_count, 0);
  return `${works.toLocaleString('en')} works · ${volumes.toLocaleString('en')} vols`;
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
      {domains.loading ? <Spinner label="Opening the catalogue" /> : null}
      {domains.error ? (
        <Text as="p" size="sm" tone="danger">
          Could not load the catalogue: {domains.error.message}
        </Text>
      ) : null}
      {domains.data ? (
        <ol className="fihrist__list">
          {domains.data.map((d) => (
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
      ) : null}
    </section>
  );
}
