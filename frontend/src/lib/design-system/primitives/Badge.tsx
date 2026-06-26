import type { ReactNode } from 'react';
import { cx } from '../../utils';
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
  dir?: 'rtl' | 'ltr';
  className?: string;
  children: ReactNode;
}

export function Badge({ variant = 'default', dir, className, children }: BadgeProps) {
  return (
    <span dir={dir} className={cx('ds-badge', VARIANT_CLASS[variant], className)}>
      {children}
    </span>
  );
}
