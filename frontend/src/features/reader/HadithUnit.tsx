import { Badge, Highlight, NarratorLink, RefPill } from '../../lib/design-system';
import { annotateText } from '../../lib/narrators';
import type { NarratorIndex } from '../../lib/narrators';
import type { Hadith, NarratorRecord } from '../../lib/types';
import { cx, toArabicDigits } from '../../lib/utils';
import { hadithBadge } from '../../lib/variants';
import type { ReaderLang } from './ReaderToolbar';

// The unit noun the card head shows, by the book's domain: the same card
// carries a hadith, a Qurʾān verse, or a fiqh ruling.
export const UNIT_NOUNS: Record<string, string> = {
  quran: 'Verse',
  hadith: 'Hadith',
  fiqh: 'Ruling',
};
export const UNIT_NOUN_DEFAULT = 'Passage';

export interface HadithUnitProps {
  h: Hadith;
  noun: string;
  active: boolean;
  lang: ReaderLang;
  index: NarratorIndex;
  activeNarrator: string;
  highlight: string;
  onSelect: () => void;
  onNarrator: (record: NarratorRecord) => void;
}

/** One structured unit card on a reader page: isnād with narrator links, matn
    in the active language mode, grade badge, and parallel-narration pills. */
export function HadithUnit({
  h,
  noun,
  active,
  lang,
  index,
  activeNarrator,
  highlight,
  onSelect,
  onNarrator,
}: HadithUnitProps) {
  const segs = annotateText(h.isnad_ar, index);
  return (
    <section className={cx('hadith', active && 'hadith--active')} tabIndex={0} onClick={onSelect}>
      <header className="hadith__head">
        <span className="hadith__id">
          <span className="hadith__num">{toArabicDigits(h.n)}</span>
          <span className="hadith__meta">
            {noun} {h.n}
            {h.narrators.length > 0 ? ` · ${h.narrators.length} narrators` : ''}
          </span>
        </span>
        {h.grade ? (
          <Badge surface="reader" variant={hadithBadge(h.grade)} dot dir="rtl">
            {h.grade}
          </Badge>
        ) : null}
      </header>
      {lang !== 'en' && h.isnad_ar ? (
        <p className="hadith__isnad" dir="rtl">
          {segs.map((s, i) =>
            s.type === 'narrator' ? (
              <NarratorLink
                key={i}
                active={activeNarrator === s.record.full_name}
                onActivate={() => onNarrator(s.record)}
              >
                {s.value}
              </NarratorLink>
            ) : (
              <span key={i}>{s.value}</span>
            ),
          )}
        </p>
      ) : null}
      <div className={cx('hadith__body', lang === 'both' && 'hadith__body--grid')}>
        {lang !== 'ar' && h.matn_en ? (
          <p className="hadith__matn-en">
            <Highlight text={h.matn_en} query={highlight} />
          </p>
        ) : null}
        {lang !== 'en' ? (
          <p className="hadith__matn-ar" dir="rtl">
            <Highlight text={h.matn_ar} query={highlight} />
          </p>
        ) : null}
      </div>
      {h.cross_refs.length ? (
        <div className="hadith__refs">
          <span className="hadith__refs-label">Parallels</span>
          {h.cross_refs.map((r, i) => (
            <RefPill key={i} ar={r.book_ar} label={r.page ? String(r.page) : null} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
