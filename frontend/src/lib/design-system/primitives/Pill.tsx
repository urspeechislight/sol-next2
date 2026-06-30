import type { ReactNode } from 'react';
import { cx } from '../../utils';
import { Icon } from './Icon';
import type { IconName } from '../internal/icons';
import type { Surface } from './IconButton';
import './Pill.css';

export interface PillProps {
  children: ReactNode;
  icon?: IconName;
  active?: boolean;
  surface?: Surface;
  /** Render as a non-interactive display (a status pill), not a button. */
  display?: boolean;
  /** Show the pill's surface, its background and border, at rest rather than
      only on hover or active. Use for a standing control like the back button. */
  raised?: boolean;
  ariaLabel?: string;
  className?: string;
  onClick?: () => void;
}

/** A pill: an icon-optional, toggle-able chip. The one source for the pill
    pattern the reader used (drawer toggles, the page indicator). */
export function Pill({
  children,
  icon,
  active = false,
  surface = 'app',
  display = false,
  raised = false,
  ariaLabel,
  className,
  onClick,
}: PillProps) {
  const cls = cx(
    'ds-pill',
    `ds-pill--${surface}`,
    active && 'ds-pill--on',
    raised && 'ds-pill--raised',
    className,
  );
  const body = (
    <>
      {icon ? <Icon name={icon} size="sm" /> : null}
      {children}
    </>
  );
  if (display) {
    return (
      <span className={cls} aria-label={ariaLabel}>
        {body}
      </span>
    );
  }
  return (
    <button
      type="button"
      className={cls}
      aria-label={ariaLabel}
      aria-pressed={active}
      onClick={onClick}
    >
      {body}
    </button>
  );
}
