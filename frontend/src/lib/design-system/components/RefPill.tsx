import './RefPill.css';

export interface RefPillProps {
  /** Arabic source name, the pill's reading voice. */
  ar: string;
  /** Mono locator beside the name: a hadith number, a page. Omit when the
      citation has none. */
  label?: string | null;
}

/** A source-citation pill: the Arabic book name plus a mono locator, themed
    with the reader palette. The one citation-chip markup (the hadith block's
    cross-references, the daily hadith's source), so the pill cannot fork per
    feature. Wrap it in a button when the citation is a navigation target. */
export function RefPill({ ar, label }: RefPillProps) {
  return (
    <span className="ds-refpill">
      <span className="ds-refpill__ar" dir="rtl">
        {ar}
      </span>
      {label ? <span className="ds-refpill__pg">{label}</span> : null}
    </span>
  );
}
