import type { ReactNode } from 'react';
import { UnstyledButton } from '../primitives/UnstyledButton';
import './IndexRow.css';

export interface IndexRowProps {
  /** English label, the row's reading voice. */
  en: string;
  /** Arabic display label, set on the spine side. */
  ar: string;
  /** Optional one-line description under the English label. */
  blurb?: string | null;
  /** Mono margin annotation, e.g. "1,207 works · 2,412 vols". */
  meta: string;
  /** Anchor mode: the row is a link (hash navigation). */
  href?: string;
  /** Button mode: the row is an in-app action. Ignored when href is set. */
  onActivate?: () => void;
  /** Toggle mode (button only): the row is the active scope; renders the
      accent-tint pressed state and aria-pressed, e.g. a search work-head
      whose activation narrows the stream to that work. */
  current?: boolean;
  ariaLabel?: string;
}

function RowBody({ en, ar, blurb, meta }: Pick<IndexRowProps, 'en' | 'ar' | 'blurb' | 'meta'>) {
  return (
    <>
      <span className="ds-idxrow__labels">
        <span className="ds-idxrow__en">{en}</span>
        {blurb ? <span className="ds-idxrow__blurb">{blurb}</span> : null}
      </span>
      <span className="ds-idxrow__leader" aria-hidden="true" />
      <span className="ds-idxrow__meta">{meta}</span>
      <span className="ds-idxrow__ar" dir="rtl">
        {ar}
      </span>
    </>
  );
}

/** One contents-page row — the fihrist grammar shared by the landing page's
    domain band and the library's index panes: English label (+ optional
    blurb), dotted leader, mono annotation in the margin, Arabic display label
    on the spine side, gold wash on hover. Renders as an anchor when ``href``
    is given (URL navigation), otherwise as a button, optionally carrying a
    pressed "current scope" state. */
export function IndexRow({
  en,
  ar,
  blurb,
  meta,
  href,
  onActivate,
  current,
  ariaLabel,
}: IndexRowProps) {
  const body: ReactNode = <RowBody en={en} ar={ar} blurb={blurb} meta={meta} />;
  if (href) {
    return (
      <a className="ds-idxrow" href={href} aria-label={ariaLabel}>
        {body}
      </a>
    );
  }
  return (
    <UnstyledButton
      className={current ? 'ds-idxrow ds-idxrow--current' : 'ds-idxrow'}
      onClick={onActivate}
      ariaPressed={current}
      ariaLabel={ariaLabel}
    >
      {body}
    </UnstyledButton>
  );
}
