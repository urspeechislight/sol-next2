import type { ReactNode } from 'react';
import { Highlight } from '../primitives/Highlight';
import { Link } from '../primitives/Link';
import { NewTabLink } from '../primitives/NewTabLink';
import './SourceRecord.css';

export interface SourceRecordProps {
  /** Resolved category label, e.g. "Tafsīr" (the parent maps the slug). */
  section: string;
  titleAr: string;
  titleEn: string | null;
  author: string | null;
  /** Arabic author shown under the Arabic title (books + works). Omit for a
      passage hit, whose body carries the matched snippet instead. */
  authorAr?: string | null;
  /** Meta badges on the English spine: a page reference for a passage, or the
      volume / sect / death / page badges for a book or work. */
  badges?: ReactNode;
  /** Matched passage for a content hit; when present it fills the Arabic body
      (highlighted) in place of the Arabic author. */
  snippet?: string;
  query?: string;
  /** Real href for this hit: a plain click drills in place (onOpen), while
      ctrl/cmd/middle-click and the adjacent NewTabLink open it fresh, exactly
      like the content scope's passage rows. */
  href: string;
  onOpen: () => void;
}

/** The one bilingual two-zone result record, shared by content search, book
    search, and the library: an English reference spine on the left (section,
    romanized title, author, meta badges) and the Arabic title with either the
    matched passage or the Arabic author on the right. English always left,
    Arabic always right. */
export function SourceRecord({
  section,
  titleAr,
  titleEn,
  author,
  authorAr,
  badges,
  snippet,
  query,
  href,
  onOpen,
}: SourceRecordProps) {
  const label = titleEn ?? titleAr;
  return (
    <div className="ds-record-row">
      <Link href={href} onActivate={onOpen} className="ds-record" ariaLabel={`Open ${label}`}>
        <span className="ds-record__spine">
          <span className="ds-record__sec">{section}</span>
          {titleEn ? <span className="ds-record__title-en">{titleEn}</span> : null}
          {author ? <span className="ds-record__author">{author}</span> : null}
          {badges ? <span className="ds-record__badges">{badges}</span> : null}
        </span>
        <span className="ds-record__body" dir="rtl">
          <span className="ds-record__title-ar">{titleAr}</span>
          {snippet !== undefined ? (
            <span className="ds-record__snip">
              <Highlight text={snippet} query={query ?? ''} />
            </span>
          ) : authorAr ? (
            <span className="ds-record__author-ar">{authorAr}</span>
          ) : null}
        </span>
      </Link>
      <NewTabLink href={href} label={`Open ${label} in a new tab`} className="ds-record__newtab" />
    </div>
  );
}
