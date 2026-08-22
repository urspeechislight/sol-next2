import type { ReactNode } from 'react';
import './Apparatus.css';

export interface ApparatusProps {
  /** The bilingual rule label, e.g. "Foundational works · أمهات الكتب". */
  children: ReactNode;
  /** Optional mono marginalia after the label, e.g. "6 of 31". */
  marginalia?: ReactNode;
}

/** The section grammar, app-wide: a centered mono label between two fading
    gold hairlines, with optional marginalia. The one rule-with-label markup —
    the library's sections and the landing folio's bands all rule through it,
    so no feature re-implements the hairline pair. */
export function Apparatus({ children, marginalia }: ApparatusProps) {
  return (
    <div className="apparatus">
      <span className="apparatus__label">{children}</span>
      {marginalia ? <span className="apparatus__margin">{marginalia}</span> : null}
    </div>
  );
}
