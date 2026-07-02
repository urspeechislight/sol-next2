import type { ReactNode } from 'react';
import { cx } from '../../utils';
import './Eyebrow.css';

export type EyebrowTracking = 'normal' | 'wide' | 'section';

export interface EyebrowProps {
  /** Letter-spacing step; the values live in Eyebrow.css, nowhere else. */
  tracking?: EyebrowTracking;
  /** 'accent' (default) for section labels, 'muted' for quiet crumbs. */
  tone?: 'accent' | 'muted';
  className?: string;
  children: ReactNode;
}

/** The small tracked uppercase label that opens a panel or section. One
    definition of the eyebrow's type, casing, and tracking scale — features
    position it, never restyle it. */
export function Eyebrow({ tracking = 'normal', tone = 'accent', className, children }: EyebrowProps) {
  return (
    <span
      className={cx(
        'ds-eyebrow',
        tracking !== 'normal' && `ds-eyebrow--${tracking}`,
        tone === 'muted' && 'ds-eyebrow--muted',
        className,
      )}
    >
      {children}
    </span>
  );
}
