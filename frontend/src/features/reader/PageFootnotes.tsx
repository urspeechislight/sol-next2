import { FootnoteRef } from '../../lib/design-system';
import type { Footnote } from '../../lib/types';
import type { ReaderLang } from './ReaderToolbar';

/** The apparatus annotates the Arabic text and has no translation; the EN-mode
    label says so in English instead of leaving an unexplained Arabic block. */
const LABELS: Record<ReaderLang, string> = {
  ar: 'الحواشي',
  both: 'الحواشي · Edition notes',
  en: 'Edition notes · in the original Arabic, untranslated',
};

export interface PageFootnotesProps {
  footnotes: Footnote[];
  /** Entry numbers whose marker occurs in the page body: only these link back.
      An entry with no matched marker renders a plain, non-interactive number,
      never a control that looks clickable and does nothing. */
  linked: ReadonlySet<string>;
  lang: ReaderLang;
  onBacklink: (marker: string) => void;
}

/** Scroll the first match of ``selector`` under ``root`` into view and replay
    its pulse wash. The reader shows one page at a time, so the first match IS
    the page's element; duplicate same-N markers deliberately resolve to the
    first printed occurrence (1.8% of corpus pages). */
export function pulseFootnoteTarget(root: HTMLElement | null, selector: string): void {
  if (!root) return;
  const el = root.querySelector<HTMLElement>(selector);
  if (!el) return;
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  el.classList.remove('fn-pulse');
  void el.offsetWidth;
  el.classList.add('fn-pulse');
}

/** The page's footnote apparatus: the editor's notes as printed at the foot of
    the page, in printed order. Unnumbered entries (free-form blocks, or the
    continuation of the previous page's note in continuously numbered editions)
    render as text without a number. Rendered in every language mode: the notes
    are served scholarly content, and hiding them in EN mode would be the
    forbidden silent omission. */
export function PageFootnotes({ footnotes, linked, lang, onBacklink }: PageFootnotesProps) {
  if (footnotes.length === 0) return null;
  return (
    <aside className="reader-footnotes" role="doc-endnotes" aria-label="Footnotes">
      <p className="reader-footnotes__label">{LABELS[lang]}</p>
      <ul className="reader-footnotes__list" dir="rtl">
        {footnotes.map((f, i) => (
          <li key={i} className="reader-footnotes__entry" data-fn-entry={f.marker ?? undefined}>
            {f.marker !== null ? (
              linked.has(f.marker) ? (
                <FootnoteRef
                  variant="entry"
                  label={`Back to footnote marker ${f.marker}`}
                  onActivate={() => onBacklink(f.marker as string)}
                >
                  ({f.marker})
                </FootnoteRef>
              ) : (
                <span className="reader-footnotes__num">({f.marker})</span>
              )
            ) : null}
            <span className="reader-footnotes__text">{f.text}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
