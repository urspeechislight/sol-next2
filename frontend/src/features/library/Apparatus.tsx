import type { ReactNode } from 'react';
import './Apparatus.css';

export interface ApparatusProps {
  /** The bilingual rule label, e.g. "Foundational works · أمهات الكتب". */
  children: ReactNode;
  /** Optional mono marginalia after the label, e.g. "6 of 31". */
  marginalia?: ReactNode;
}

/** The library's section grammar, matching the landing folio: a centered mono
    label between two fading gold hairlines, with optional marginalia. */
export function Apparatus({ children, marginalia }: ApparatusProps) {
  return (
    <div className="apparatus">
      <span className="apparatus__label">{children}</span>
      {marginalia ? <span className="apparatus__margin">{marginalia}</span> : null}
    </div>
  );
}
