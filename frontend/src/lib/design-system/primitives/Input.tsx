import { cx } from "../../utils";
import { Icon } from "./Icon";
import type { IconName } from "../internal/icons";
import "./Input.css";

export interface InputProps {
  value: string;
  label?: string;
  hideLabel?: boolean;
  id?: string;
  placeholder?: string;
  type?: "text" | "search";
  icon?: IconName;
  disabled?: boolean;
  dir?: "rtl" | "ltr";
  ariaLabel?: string;
  className?: string;
  onInput?: (value: string) => void;
}

/** Composite field: ds-field > label + ds-input(container) > icon + ds-input__field. */
export function Input({
  value, label, hideLabel = false, id, placeholder, type = "text", icon,
  disabled = false, dir, ariaLabel, className, onInput,
}: InputProps) {
  return (
    <div className={cx("ds-field", className)}>
      {label ? (
        <label htmlFor={id} className={cx("ds-field__label", hideLabel && "ds-field__label--hidden")}>
          {label}
        </label>
      ) : null}
      <div className="ds-input">
        {icon ? <Icon name={icon} size="sm" className="ds-input__icon" /> : null}
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
      </div>
    </div>
  );
}
