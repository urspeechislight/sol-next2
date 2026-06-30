import type { ReactNode } from 'react';
import { cx } from '../../utils';
import type { Surface } from './IconButton';
import './Badge.css';

export type BadgeVariant = 'default' | 'success' | 'warning' | 'danger';

const VARIANT_CLASS: Record<BadgeVariant, string> = {
  default: 'ds-badge--default',
  success: 'ds-badge--success',
  warning: 'ds-badge--warning',
  danger: 'ds-badge--danger',
};

export interface BadgeProps {
  variant?: BadgeVariant;
  /** "reader" themes the badge for the reading surface: pill, uppercase, dot. */
  surface?: Surface;
  /** Leading status dot, a quiet grade cue on the reading surface. */
  dot?: boolean;
  dir?: 'rtl' | 'ltr';
  className?: string;
  children: ReactNode;
}

export function Badge({
  variant = 'default',
  surface = 'app',
  dot = false,
  dir,
  className,
  children,
}: BadgeProps) {
  return (
    <span
      dir={dir}
      className={cx(
        'ds-badge',
        surface === 'reader' && 'ds-badge--reader',
        VARIANT_CLASS[variant],
        className,
      )}
    >
      {dot ? <i className="ds-badge__dot" /> : null}
      {children}
    </span>
  );
}
