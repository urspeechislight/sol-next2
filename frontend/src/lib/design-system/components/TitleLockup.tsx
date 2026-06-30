import { cx } from '../../utils';
import './TitleLockup.css';

export type LockupMode = 'en' | 'both' | 'ar';

export interface TitleLockupProps {
  titleAr: string;
  titleEn?: string | null;
  author?: string | null;
  mode: LockupMode;
  className?: string;
}

/** Bilingual reader title: each script on its own line and its own direction,
    answering the EN / EN|AR / AR language mode. The Arabic is the display face;
    the English drops to an italic subtitle and the author to an upright byline —
    never strung onto one baseline with bullets (Issue 01, Direction A+C). */
export function TitleLockup({ titleAr, titleEn, author, mode, className }: TitleLockupProps) {
  if (mode === 'en') {
    return (
      <div className={cx('ds-lockup', className)}>
        <div className="ds-lockup__en-primary">{titleEn ?? titleAr}</div>
        {author ? <div className="ds-lockup__byline">{author}</div> : null}
      </div>
    );
  }
  return (
    <div className={cx('ds-lockup', className)}>
      <div className="ds-lockup__ar" dir="rtl">
        {titleAr}
      </div>
      {mode === 'both' && (titleEn || author) ? (
        <div className="ds-lockup__sub">
          {titleEn ? <span className="ds-lockup__sub-title">{titleEn}</span> : null}
          {titleEn && author ? <span aria-hidden="true"> · </span> : null}
          {author ? <span className="ds-lockup__byline-inline">{author}</span> : null}
        </div>
      ) : null}
      {mode === 'ar' && author ? <div className="ds-lockup__byline">{author}</div> : null}
    </div>
  );
}
