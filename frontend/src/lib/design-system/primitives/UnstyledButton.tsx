import type { CSSProperties, ReactNode } from 'react';
import { cx } from '../../utils';
import './UnstyledButton.css';

export interface UnstyledButtonProps {
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  ariaLabel?: string;
  /** Toggle state; 'mixed' marks a partially-applied group toggle. */
  ariaPressed?: boolean | 'mixed';
  /** Disclosure state for expand/collapse triggers. */
  ariaExpanded?: boolean;
  title?: string;
  tabIndex?: number;
  style?: CSSProperties;
  children?: ReactNode;
}

/** The bare pressable: a real button with the design system's focus ring and
    no other chrome. Features compose custom interactive surfaces (cards,
    pills, dots, cartouches) on top of it instead of styling raw buttons —
    keeping semantics and focus behaviour in one place. */
export function UnstyledButton({
  className,
  onClick,
  disabled = false,
  ariaLabel,
  ariaPressed,
  ariaExpanded,
  title,
  tabIndex,
  style,
  children,
}: UnstyledButtonProps) {
  return (
    <button
      type="button"
      className={cx('ds-unbtn', className)}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      aria-pressed={ariaPressed}
      aria-expanded={ariaExpanded}
      title={title}
      tabIndex={tabIndex}
      style={style}
    >
      {children}
    </button>
  );
}
