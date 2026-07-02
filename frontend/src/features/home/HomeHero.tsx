import { Badge, Button, Eyebrow, Highlight, Text } from '../../lib/design-system';
import type { Domain } from '../../lib/types';
import { hadithBadge } from '../../lib/variants';
import { sumCount } from '../library/lib';
import '../../components/HadithBlock.css';
import './HomeHero.css';

export interface HomeHeroProps {
  domains: Domain[];
  onBrowse: () => void;
  onToday: () => void;
}

/** The landing hero on the illuminated canvas: editorial copy overlapping a
    real reading artifact — the opening hadith of Ṣaḥīḥ al-Bukhārī in the
    classical reader dress. Proof of what the instrument does, not claims. */
export function HomeHero({ domains, onBrowse, onToday }: HomeHeroProps) {
  const works = domains.reduce((total, d) => total + sumCount(d.categories), 0);
  return (
    <section className="hhero" aria-label="Welcome">
      <div className="hhero__copy">
        <Eyebrow tracking="wide" className="hhero__eyebrow">
          <span className="hhero__eyebrow-mark" aria-hidden="true" />
          Sol · a reading instrument for the classical tradition
        </Eyebrow>
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

      <div
        className="hhero__artifact"
        data-reader-theme="classical"
        aria-label="Example reading: the opening hadith of Ṣaḥīḥ al-Bukhārī"
      >
        <div className="hadith__head">
          <span className="hhero__artifact-id">
            <span className="hadith__num">١</span>
            Ṣaḥīḥ al-Bukhārī · Kitāb al-Īmān
          </span>
          <Badge surface="reader" variant={hadithBadge('sahih')} dot>
            ṣaḥīḥ
          </Badge>
        </div>
        <Text as="p" font="arabic" dir="rtl" className="hhero__artifact-isnad">
          حَدَّثَنَا عَبْدُ اللَّهِ بْنُ مَسْلَمَةَ الْقَعْنَبِيُّ، عَنْ مَالِكٍ
        </Text>
        <Text as="p" font="arabic" dir="rtl" className="hhero__artifact-matn">
          <Highlight
            text="إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى"
            query="النيات"
          />
        </Text>
        <Text as="p" className="hhero__artifact-en">
          “Actions are but by intentions, and each person shall have only what they intended.”
        </Text>
      </div>
    </section>
  );
}
