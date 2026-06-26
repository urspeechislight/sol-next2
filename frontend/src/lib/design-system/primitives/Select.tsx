import { cx } from "../../utils";
import "./Select.css";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps {
  value: string;
  options: SelectOption[];
  disabled?: boolean;
  ariaLabel?: string;
  className?: string;
  onChange?: (value: string) => void;
}

export function Select({ value, options, disabled = false, ariaLabel, className, onChange }: SelectProps) {
  return (
    <select
      value={value}
      disabled={disabled}
      aria-label={ariaLabel}
      className={cx("ds-select", className)}
      onChange={(e) => onChange?.(e.target.value)}
    >
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}
