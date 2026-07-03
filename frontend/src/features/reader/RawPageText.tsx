import { CiteLink, FootnoteRef, Highlight } from '../../lib/design-system';
import { citationSegments } from '../../lib/citations';
import { footnoteSegments } from '../../lib/footnotes';
import { flowBlocks } from '../../lib/paragraphs';
import type { FlowBlock } from '../../lib/paragraphs';
import type { QuranCitation } from '../../lib/types';
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
  /** Offset-anchored Quran citations resolved for this page's text_ar. */
  citations: readonly QuranCitation[];
  onCite: (surah: number, aya: number) => void;
}

interface ArabicBodyProps {
  text: string;
  highlight: string;
  markers: ReadonlySet<string>;
  onMarker: (marker: string) => void;
  citations: readonly QuranCitation[];
  onCite: (surah: number, aya: number) => void;
}

/** One display block: citation splitting runs first (its ranges are
    offset-anchored and authoritative, rebased to the block), footnote-marker
    splitting inside the remaining text, search highlighting inside each text
    segment. The three segmenters never fight over one range. */
function ArabicBlock({
  block,
  highlight,
  markers,
  onMarker,
  citations,
  onCite,
}: ArabicBodyProps & { block: FlowBlock }) {
  const local = citations
    .filter(
      (c) => c.offset >= block.start && c.offset + c.length <= block.start + block.text.length,
    )
    .map((c) => ({ ...c, offset: c.offset - block.start }));
  return (
    <p className="reader-rawtext">
      {citationSegments(block.text, local).map((cs, i) =>
        cs.type === 'cite' ? (
          <CiteLink
            key={i}
            label={`Open Quran ${cs.surah}:${cs.ayaStart}`}
            onActivate={() => onCite(cs.surah, cs.ayaStart)}
          >
            {cs.value}
          </CiteLink>
        ) : (
          <span key={i}>
            {footnoteSegments(cs.value, markers).map((seg, j) =>
              seg.type === 'marker' ? (
                <FootnoteRef
                  key={j}
                  label={`Footnote ${seg.marker}`}
                  refMarker={seg.marker}
                  onActivate={() => onMarker(seg.marker)}
                >
                  {seg.value}
                </FootnoteRef>
              ) : (
                <Highlight key={j} text={seg.value} query={highlight} />
              ),
            )}
          </span>
        ),
      )}
    </p>
  );
}

/** The Arabic column, one block per structural break (blank lines, short
    standalone lines, terminal punctuation): print-margin newlines stay inside
    the block text and flow under white-space: normal, so sentences no longer
    hard-break mid-line in narrow columns. Block text is an exact slice of the
    page text, so the footnote tokenizer's line-start rule and the citations'
    offsets both stay anchored. */
function ArabicBody(props: ArabicBodyProps) {
  return (
    <div className="reader-rawtext-blocks" dir="rtl">
      {flowBlocks(props.text).map((block) => (
        <ArabicBlock key={block.start} block={block} {...props} />
      ))}
    </div>
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
  citations,
  onCite,
}: RawPageTextProps) {
  const arabic = (
    <ArabicBody
      text={textAr}
      highlight={highlight}
      markers={markers}
      onMarker={onMarker}
      citations={citations}
      onCite={onCite}
    />
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
