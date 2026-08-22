import { cx } from '../../utils';

import './RefPill.css';

export interface RefPillProps {
  /** Arabic source name, the pill's reading voice. */
  ar: string;
  /** Mono locator beside the name: a hadith number, a page. Omit when the
      citation has none. */
  label?: string | null;
  /** 'reader' (default) themes with the reader palette and requires a
      [data-reader-theme] ancestor; 'app' re-points the pill to the
      app-surface palette for use outside reading scopes (home folio). */
  surface?: 'app' | 'reader';
}

/** A source-citation pill: the Arabic book name plus a mono locator, themed
    with the reader palette. The one citation-chip markup (the hadith block's
    cross-references, the daily hadith's source), so the pill cannot fork per
    feature. Wrap it in a button when the citation is a navigation target. */
export function RefPill({ ar, label, surface = 'reader' }: RefPillProps) {
  return (
    <span className={cx('ds-refpill', surface === 'app' && 'ds-refpill--app')}>
      <span className="ds-refpill__ar" dir="rtl">
        {ar}
      </span>
      {label ? <span className="ds-refpill__pg">{label}</span> : null}
    </span>
  );
}
