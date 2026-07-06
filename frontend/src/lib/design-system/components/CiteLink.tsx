import type { ReactNode } from 'react';
import './CiteLink.css';

export interface CiteLinkProps {
  /** Accessible name, e.g. "Open Quran 2:30". */
  label: string;
  onActivate: () => void;
  children: ReactNode;
}

/** A Qurʾān citation woven into reader text: the children ARE the printed
    reference glyphs, kept in place and never rewritten, marked as a verse
    link that opens the Qurʾān reader. Stops propagation so a click never
    also triggers an enclosing unit. */
export function CiteLink({ label, onActivate, children }: CiteLinkProps) {
  return (
    <button
      type="button"
      className="ds-cite"
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
