import type { ReactNode } from 'react';
import { cx } from '../../utils';
import { Icon } from './Icon';
import type { IconName } from '../internal/icons';
import './Button.css';

export type ButtonVariant = 'primary' | 'secondary' | 'gold' | 'ghost' | 'link';
export type ButtonSize = 'sm' | 'md';

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary: 'ds-btn--primary',
  secondary: 'ds-btn--secondary',
  gold: 'ds-btn--gold',
  ghost: 'ds-btn--ghost',
  link: 'ds-btn--link',
};
const SIZE_CLASS: Record<ButtonSize, string> = { sm: 'ds-btn--sm', md: 'ds-btn--md' };

export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  type?: 'button' | 'submit';
  disabled?: boolean;
  block?: boolean;
  iconBefore?: IconName;
  iconAfter?: IconName;
  ariaLabel?: string;
  ariaPressed?: boolean;
  onClick?: () => void;
  children?: ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  type = 'button',
  disabled = false,
  block = false,
  iconBefore,
  iconAfter,
  ariaLabel,
  ariaPressed,
  onClick,
  children,
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled}
      aria-label={ariaLabel}
      aria-pressed={ariaPressed}
      onClick={onClick}
      className={cx('ds-btn', VARIANT_CLASS[variant], SIZE_CLASS[size], block && 'ds-btn--block')}
    >
      {iconBefore ? <Icon name={iconBefore} size="sm" /> : null}
      {children ? <span className="ds-btn__label">{children}</span> : null}
      {iconAfter ? <Icon name={iconAfter} size="sm" /> : null}
    </button>
  );
}
