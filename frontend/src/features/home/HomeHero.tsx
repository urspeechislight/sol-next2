import { Button } from '../../lib/design-system';
import type { Domain } from '../../lib/types';
import { sumCount } from '../library/lib';
import { Astrolabe } from './Astrolabe';
import './HomeHero.css';

export interface HomeHeroProps {
  domains: Domain[];
  onOpenDomain: (id: string) => void;
  onBrowse: () => void;
  onToday: () => void;
}

/** The landing hero on the celestial canvas: editorial copy over the night
    sky beside the astrolabe of domains. Text overlays the glow; the
    instrument is the door into the Library. */
export function HomeHero({ domains, onOpenDomain, onBrowse, onToday }: HomeHeroProps) {
  const works = domains.reduce((total, d) => total + sumCount(d.categories), 0);
  return (
    <section className="hhero" aria-label="Welcome">
      <div className="hhero__copy">
        <p className="hhero__eyebrow">
          <span className="hhero__eyebrow-mark" aria-hidden="true" />
          Sol · a reading instrument for the classical tradition
        </p>
        <h1 className="hhero__h1">
          Read the sources.
          <br />
          <em>Trace the chains.</em>
        </h1>
        <p className="hhero__salawat" dir="rtl">
          اللهم صل على محمد وآل محمد
        </p>
        <p className="hhero__lede">
          {works > 0 ? `${works.toLocaleString()} works of ` : ''}hadith, tafsīr, fiqh and history,
          read Arabic-first with English alongside — every isnād one tap from its transmission
          chain, every narrator one tap from his tarjama.
        </p>
        <div className="hhero__cta">
          <Button variant="gold" iconBefore="daily" onClick={onToday}>
            Today’s reading
          </Button>
          <Button variant="ghost" iconAfter="arrow-right" onClick={onBrowse}>
            Browse the library
          </Button>
        </div>
      </div>
      <div className="hhero__instrument">
        <Astrolabe domains={domains} onPickDomain={onOpenDomain} />
      </div>
    </section>
  );
}
