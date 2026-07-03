import { FootnoteRef, Highlight } from '../../lib/design-system';
import { footnoteSegments } from '../../lib/footnotes';
import type { ReaderLang } from './ReaderToolbar';

const PLACEHOLDER_EN =
  'An English translation for this page has not been added to the corpus yet. ' +
  'This preview shows how it will read: the translation sits in this column in the ' +
  'same serif face as the Arabic, justified and aligned paragraph for paragraph. ' +
  'When a translation is ingested it replaces this note and appears here exactly as shown.';

export interface RawPageTextProps {
  textAr: string;
  textEn: string | null;
  lang: ReaderLang;
  highlight: string;
  /** Numbered apparatus entries on this page; body candidates outside this set stay text. */
  markers: ReadonlySet<string>;
  onMarker: (marker: string) => void;
}

interface ArabicBodyProps {
  text: string;
  highlight: string;
  markers: ReadonlySet<string>;
  onMarker: (marker: string) => void;
}

/** The Arabic column: footnote markers wrapped (printed glyphs kept, styled
    gold and raised) and everything else highlighted for in-book search. The
    marker split runs first, the search highlight inside each text segment, so
    the two segmenters never fight over one range. */
function ArabicBody({ text, highlight, markers, onMarker }: ArabicBodyProps) {
  return (
    <p className="reader-rawtext" dir="rtl">
      {footnoteSegments(text, markers).map((seg, i) =>
        seg.type === 'marker' ? (
          <FootnoteRef
            key={i}
            label={`Footnote ${seg.marker}`}
            refMarker={seg.marker}
            onActivate={() => onMarker(seg.marker)}
          >
            {seg.value}
          </FootnoteRef>
        ) : (
          <Highlight key={i} text={seg.value} query={highlight} />
        ),
      )}
    </p>
  );
}

/** Raw (un-parsed) page text, rendered for the active language mode. AR shows the
    Arabic alone; EN shows the English alone; EN | AR shows English (serif) beside
    Arabic. The English column carries a real translation (text_en) when the corpus
    has one, or a labelled preview until then — both through the same elements, so a
    real translation drops in identically. The preview is never highlighted. */
export function RawPageText({
  textAr,
  textEn,
  lang,
  highlight,
  markers,
  onMarker,
}: RawPageTextProps) {
  const arabic = (
    <ArabicBody text={textAr} highlight={highlight} markers={markers} onMarker={onMarker} />
  );
  if (lang === 'ar') {
    return arabic;
  }
  const hasEn = Boolean(textEn);
  const enText = textEn ? textEn : PLACEHOLDER_EN;
  const enHighlight = hasEn ? highlight : '';
  const draft = hasEn ? null : <span className="reader-draft-tag">English preview</span>;
  if (lang === 'en') {
    return (
      <>
        {draft}
        <p className="reader-en-only">
          <Highlight text={enText} query={enHighlight} />
        </p>
      </>
    );
  }
  return (
    <>
      {draft}
      <div className="reader-bi">
        <p className="reader-bi__en">
          <Highlight text={enText} query={enHighlight} />
        </p>
        {arabic}
      </div>
    </>
  );
}
