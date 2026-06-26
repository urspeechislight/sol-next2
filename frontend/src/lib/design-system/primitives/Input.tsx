import { cx } from "../../utils";
import "./Input.css";

export interface InputProps {
  value: string;
  placeholder?: string;
  type?: "text" | "search";
  disabled?: boolean;
  invalid?: boolean;
  dir?: "rtl" | "ltr";
  ariaLabel?: string;
  className?: string;
  onInput?: (value: string) => void;
}

export function Input({ value, placeholder, type = "text", disabled = false, invalid = false, dir, ariaLabel, className, onInput }: InputProps) {
  return (
    <input
      type={type}
      value={value}
      placeholder={placeholder}
      disabled={disabled}
      dir={dir}
      aria-label={ariaLabel}
      aria-invalid={invalid || undefined}
      className={cx("ds-input", invalid && "ds-input--invalid", className)}
      onInput={(e) => onInput?.((e.target as HTMLInputElement).value)}
    />
  );
}
