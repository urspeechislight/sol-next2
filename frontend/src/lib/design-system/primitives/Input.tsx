import type { ReactNode } from 'react';
import { cx } from '../../utils';
import { Icon } from './Icon';
import type { IconName } from '../internal/icons';
import type { Surface } from '../surfaces';
import './Input.css';

export interface InputProps {
  value: string;
  label?: string;
  hideLabel?: boolean;
  id?: string;
  placeholder?: string;
  type?: 'text' | 'search';
  icon?: IconName;
  leading?: ReactNode;
  surface?: Surface;
  disabled?: boolean;
  dir?: 'rtl' | 'ltr';
  ariaLabel?: string;
  className?: string;
  onInput?: (value: string) => void;
  /** Make the field a search form: Enter (or clicking the icon) fires this once,
      instead of any live/per-keystroke behavior the caller wires to onInput. */
  onSubmit?: () => void;
  /** When set, a trailing clear button appears once the field has text and calls
      this. Lets a live search reset itself without leaving the field. */
  onClear?: () => void;
  clearLabel?: string;
}

/** Composite field: ds-field > label + ds-input(container) > icon + leading + field.
    ``leading`` is an optional inline control (e.g. a bare scope Select) shown
    inside the bordered container, between the icon and the text input. ``surface``
    selects the chrome: "app" (default) or "reader" (reading surface). With
    ``onSubmit`` the field becomes a search form whose icon is the submit button. */
export function Input({
  value,
  label,
  hideLabel = false,
  id,
  placeholder,
  type = 'text',
  icon,
  leading,
  surface = 'app',
  disabled = false,
  dir,
  ariaLabel,
  className,
  onInput,
  onSubmit,
  onClear,
  clearLabel = 'Clear',
}: InputProps) {
  const glyph = icon ? <Icon name={icon} size="sm" className="ds-input__icon" /> : null;
  const body = (
    <>
      {label ? (
        <label
          htmlFor={id}
          className={cx('ds-field__label', hideLabel && 'ds-field__label--hidden')}
        >
          {label}
        </label>
      ) : null}
      <div className={cx('ds-input', surface === 'reader' && 'ds-input--reader')}>
        {icon && onSubmit ? (
          <button type="submit" className="ds-input__submit" aria-label={ariaLabel ?? 'Search'}>
            {glyph}
          </button>
        ) : (
          glyph
        )}
        {leading}
        <input
          id={id}
          type={type}
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          dir={dir}
          aria-label={ariaLabel}
          className="ds-input__field"
          onInput={(e) => onInput?.((e.target as HTMLInputElement).value)}
        />
        {onClear && value ? (
          <button
            type="button"
            className="ds-input__clear"
            aria-label={clearLabel}
            onClick={onClear}
          >
            <Icon name="close" size="sm" />
          </button>
        ) : null}
      </div>
    </>
  );
  if (onSubmit) {
    return (
      <form
        className={cx('ds-field', className)}
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        {body}
      </form>
    );
  }
  return <div className={cx('ds-field', className)}>{body}</div>;
}
