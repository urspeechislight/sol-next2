import { useEffect, useRef, useState } from 'react';
import { cx } from '../../utils';
import { Icon } from './Icon';
import type { IconName } from '../internal/icons';
import type { Surface } from './IconButton';
import './Menu.css';

export interface MenuOption {
  value: string;
  label: string;
  icon?: IconName;
}

export type MenuVariant = 'default' | 'bare';

export interface MenuProps {
  value: string;
  options: MenuOption[];
  onChange: (value: string) => void;
  ariaLabel: string;
  variant?: MenuVariant;
  surface?: Surface;
  disabled?: boolean;
  className?: string;
}

/** Styled dropdown menu — the design-system replacement for a native <select>, so
    the popover renders in the product's own type/colour/radius rather than OS
    chrome. Trigger button + popover listbox with optional row icons and a check on
    the selected row. Closes on Escape, outside click, or selection. */
export function Menu({
  value,
  options,
  onChange,
  ariaLabel,
  variant = 'default',
  surface = 'app',
  disabled = false,
  className,
}: MenuProps) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const current = options.find((o) => o.value === value);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div ref={root} className={cx('ds-menu', `ds-menu--${surface}`, className)}>
      <button
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        className={cx('ds-menu__trigger', variant === 'bare' && 'ds-menu__trigger--bare')}
        onClick={() => setOpen((o) => !o)}
      >
        {current?.icon ? <Icon name={current.icon} size="sm" /> : null}
        <span className="ds-menu__label">{current?.label ?? ''}</span>
        <Icon name="chevron-down" size="sm" className="ds-menu__caret" />
      </button>
      {open ? (
        <ul className="ds-menu__list" role="listbox" aria-label={ariaLabel}>
          {options.map((o) => (
            <li key={o.value}>
              <button
                type="button"
                role="option"
                aria-selected={o.value === value}
                className={cx('ds-menu__option', o.value === value && 'ds-menu__option--on')}
                onClick={() => {
                  onChange(o.value);
                  setOpen(false);
                }}
              >
                {o.icon ? <Icon name={o.icon} size="sm" className="ds-menu__opt-icon" /> : null}
                <span className="ds-menu__opt-label">{o.label}</span>
                {o.value === value ? (
                  <Icon name="check" size="sm" className="ds-menu__check" />
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
