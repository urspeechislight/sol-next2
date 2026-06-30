import type { ReactNode } from 'react';
import { cx } from '../../utils';
import { Icon } from './Icon';
import type { Surface } from './IconButton';
import './NavArrow.css';

export type NavArrowDirection = 'back' | 'forward';
export type NavArrowSize = 'sm' | 'md';

const DIRECTION_ICON = { back: 'arrow-back', forward: 'arrow-forward' } as const;

export interface NavArrowProps {
  /** Which way the curved arrow points: back (←) or forward (→). */
  direction: NavArrowDirection;
  /** Accessible name; also the hover title when the button is icon-only. */
  label: string;
  size?: NavArrowSize;
  surface?: Surface;
  onClick?: () => void;
  /** Optional visible label beside the arrow (e.g. "Catalog"). Icon-only when omitted. */
  children?: ReactNode;
}

/** A rectangular, rounded-corner navigation button carrying the curved
    back/forward arrow. The one primitive for every "go back / go forward"
    affordance, so the shape stays uniform with the other rectangular controls
    (segmented, button, pill) across the site. */
export function NavArrow({
  direction,
  label,
  size = 'sm',
  surface = 'app',
  onClick,
  children,
}: NavArrowProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={children ? undefined : label}
      onClick={onClick}
      className={cx(
        'ds-navarrow',
        `ds-navarrow--${surface}`,
        size === 'md' && 'ds-navarrow--md',
        !children && 'ds-navarrow--icon',
      )}
    >
      <Icon name={DIRECTION_ICON[direction]} size="sm" />
      {children ? <span className="ds-navarrow__label">{children}</span> : null}
    </button>
  );
}
