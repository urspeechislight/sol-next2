import type { ReactNode } from 'react';
import './FootnoteRef.css';

export interface FootnoteRefProps {
  /** 'marker' is the raised in-text reference wrapping the printed glyphs;
      'entry' is the apparatus entry number that links back to the text. */
  variant?: 'marker' | 'entry';
  /** Accessible name, e.g. "Footnote 3" / "Back to footnote marker 3". */
  label: string;
  /** Jump-target hook: the bare entry number, emitted as data-fn-ref so the
      reader can scroll a backlink to the first printed occurrence. */
  refMarker?: string;
  onActivate: () => void;
  children: ReactNode;
}

/** A footnote reference woven into reader text, or its apparatus counterpart.
    The children ARE the printed characters («1», « 1 », (1)): the component
    styles them and never rewrites them, so selection and copy stay
    byte-identical to the corpus text. Stops propagation so a click never also
    triggers an enclosing unit. */
export function FootnoteRef({
  variant = 'marker',
  label,
  refMarker,
  onActivate,
  children,
}: FootnoteRefProps) {
  return (
    <button
      type="button"
      className={variant === 'entry' ? 'ds-fnref ds-fnref--entry' : 'ds-fnref'}
      role={variant === 'entry' ? 'doc-backlink' : 'doc-noteref'}
      data-fn-ref={refMarker}
      aria-label={label}
      onClick={(e) => {
        e.stopPropagation();
        onActivate();
      }}
    >
      {children}
    </button>
  );
}
