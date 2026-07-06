import type { ReactNode } from 'react';
import { cx, formatCount } from '../../utils';
import { Icon } from './Icon';
import './Checkbox.css';

export interface CheckboxProps {
  /** Checked, unchecked, or 'mixed' for a partially-selected group. */
  checked: boolean | 'mixed';
  onToggle: () => void;
  /** The row label. */
  children: ReactNode;
  /** Optional mono count after the label (a facet's true count). */
  count?: number;
  ariaLabel?: string;
}

/** The one multi-select row: a folio checkbox (gold check, dash when mixed)
    with a label and an optional mono count. Built as a real button with
    checkbox semantics so a filter tree is keyboard-operable for free. */
export function Checkbox({ checked, onToggle, children, count, ariaLabel }: CheckboxProps) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked === 'mixed' ? 'mixed' : checked}
      aria-label={ariaLabel}
      className={cx(
        'ds-checkbox',
        checked === true && 'ds-checkbox--on',
        checked === 'mixed' && 'ds-checkbox--mixed',
      )}
      onClick={onToggle}
    >
      <span className="ds-checkbox__box" aria-hidden="true">
        {checked === true ? <Icon name="check" size="sm" /> : null}
        {checked === 'mixed' ? <span className="ds-checkbox__dash" /> : null}
      </span>
      <span className="ds-checkbox__label">{children}</span>
      {count !== undefined ? <span className="ds-checkbox__n">{formatCount(count)}</span> : null}
    </button>
  );
}
