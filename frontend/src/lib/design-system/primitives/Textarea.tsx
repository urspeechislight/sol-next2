import { cx } from "../../utils";
import "./Textarea.css";

export interface TextareaProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  placeholder?: string;
  dir?: "rtl" | "ltr";
  hideLabel?: boolean;
  className?: string;
}

export function Textarea({
  id, label, value, onChange, rows = 2, placeholder, dir, hideLabel = false, className,
}: TextareaProps) {
  return (
    <div className={cx("ds-field", className)}>
      <label htmlFor={id} className={cx("ds-field__label", hideLabel && "ds-field__label--hidden")}>
        {label}
      </label>
      <textarea
        id={id}
        rows={rows}
        value={value}
        dir={dir}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="ds-textarea"
      />
    </div>
  );
}
