import { useRef } from 'react';
import type { KeyboardEvent } from 'react';
import { cx } from '../../utils';
import { Icon } from './Icon';
import type { IconName } from '../internal/icons';
import './Segmented.css';

export interface SegmentedOption {
  value: string;
  label: string;
  icon?: IconName;
}

export interface SegmentedProps {
  label: string;
  value: string;
  options: SegmentedOption[];
  /** "reader" themes the control with the reader surface tokens. */
  surface?: 'app' | 'reader';
  onChange: (value: string) => void;
}

export function Segmented({ label, value, options, surface = 'app', onChange }: SegmentedProps) {
  const btns = useRef<(HTMLButtonElement | null)[]>([]);

  /** The ARIA radio pattern: one tab stop for the group, arrows move both
      selection and focus (wrapping at the ends). */
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const idx = options.findIndex((o) => o.value === value);
    let next = -1;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (idx + 1) % options.length;
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp')
      next = (idx - 1 + options.length) % options.length;
    else return;
    e.preventDefault();
    const target = options[next];
    if (!target) return;
    onChange(target.value);
    btns.current[next]?.focus();
  };

  return (
    <div
      className={cx('ds-seg', surface === 'reader' && 'ds-seg--reader')}
      role="radiogroup"
      aria-label={label}
      onKeyDown={onKeyDown}
    >
      {options.map((o, i) => (
        <button
          key={o.value}
          ref={(el) => {
            btns.current[i] = el;
          }}
          type="button"
          role="radio"
          tabIndex={o.value === value ? 0 : -1}
          aria-checked={o.value === value}
          className={cx('ds-seg__btn', o.value === value && 'ds-seg__btn--on')}
          onClick={() => onChange(o.value)}
        >
          {o.icon ? <Icon name={o.icon} size="sm" /> : null}
          {o.label}
        </button>
      ))}
    </div>
  );
}
