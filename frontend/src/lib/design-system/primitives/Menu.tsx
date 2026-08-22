import { useCallback, useEffect, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { cx } from '../../utils';
import { Icon } from './Icon';
import { useDismiss } from './useDismiss';
import type { IconName } from '../internal/icons';
import type { Surface } from '../surfaces';
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
    the selected row. Closes on Escape, outside click, or selection. When a caller
    caps the list height (a long listbox that scrolls internally), opening centres
    the selected row inside the list; a list that fits untouched is never scrolled. */
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
  const list = useRef<HTMLUListElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const current = options.find((o) => o.value === value);
  const closeAndRefocus = useCallback(() => {
    setOpen(false);
    trigger.current?.focus();
  }, []);
  // Outside click just dismisses; Escape and selection return focus.
  useDismiss(root, open, useCallback(() => setOpen(false), []));

  useEffect(() => {
    if (!open) return;
    const el = list.current;
    if (!el) return;
    // Focus follows the ARIA listbox pattern: opening moves focus to the
    // selected row (first row when nothing is selected).
    const on =
      el.querySelector<HTMLElement>('.ds-menu__option--on') ??
      el.querySelector<HTMLElement>('.ds-menu__option');
    on?.focus();
    if (el.scrollHeight <= el.clientHeight) return;
    const sel = el.querySelector<HTMLElement>('.ds-menu__option--on');
    if (sel) el.scrollTop = sel.offsetTop - (el.clientHeight - sel.offsetHeight) / 2;
  }, [open]);

  const focusOption = (idx: number) => {
    const el = list.current;
    if (!el) return;
    const opts = [...el.querySelectorAll<HTMLButtonElement>('.ds-menu__option')];
    if (opts.length === 0) return;
    opts[Math.max(0, Math.min(idx, opts.length - 1))]?.focus();
  };

  const onListKeyDown = (e: KeyboardEvent<HTMLUListElement>) => {
    const el = list.current;
    if (!el) return;
    const opts = [...el.querySelectorAll<HTMLButtonElement>('.ds-menu__option')];
    const idx = opts.indexOf(document.activeElement as HTMLButtonElement);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      focusOption(idx + 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      focusOption(idx - 1);
    } else if (e.key === 'Home') {
      e.preventDefault();
      focusOption(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      focusOption(opts.length - 1);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      closeAndRefocus();
    }
  };

  const pick = (next: string) => {
    onChange(next);
    closeAndRefocus();
  };

  return (
    <div ref={root} className={cx('ds-menu', `ds-menu--${surface}`, className)}>
      <button
        ref={trigger}
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
        <ul
          ref={list}
          className="ds-menu__list"
          role="listbox"
          aria-label={ariaLabel}
          onKeyDown={onListKeyDown}
        >
          {options.map((o) => (
            <li key={o.value}>
              <button
                type="button"
                role="option"
                tabIndex={-1}
                aria-selected={o.value === value}
                className={cx('ds-menu__option', o.value === value && 'ds-menu__option--on')}
                onClick={() => pick(o.value)}
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
