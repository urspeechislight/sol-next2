import type { ReactNode } from 'react';
import { cx } from '../../utils';
import { Icon } from './Icon';
import type { IconName } from '../internal/icons';
import type { Surface } from '../surfaces';
import './Chip.css';

export interface ChipProps {
  children: ReactNode;
  icon?: IconName;
  onRemove?: () => void;
  surface?: Surface;
  dir?: 'rtl' | 'ltr';
  className?: string;
}

/** A removable filter token: label, optional leading icon, optional ✕ to drop it.
    Distinct from Badge (static) and Pill (toggle button) — a chip represents one
    active condition the user can read back and remove. */
export function Chip({ children, icon, onRemove, surface = 'app', dir, className }: ChipProps) {
  return (
    <span className={cx('ds-chip', `ds-chip--${surface}`, className)} dir={dir}>
      {icon ? <Icon name={icon} size="sm" className="ds-chip__icon" /> : null}
      <span className="ds-chip__label">{children}</span>
      {onRemove ? (
        <button
          type="button"
          className="ds-chip__remove"
          aria-label="Remove filter"
          onClick={onRemove}
        >
          <Icon name="close" size="sm" />
        </button>
      ) : null}
    </span>
  );
}
