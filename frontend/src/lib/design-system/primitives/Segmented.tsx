import { cx } from "../../utils";
import { Icon } from "./Icon";
import type { IconName } from "../internal/icons";
import "./Segmented.css";

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
  surface?: "app" | "reader";
  onChange: (value: string) => void;
}

export function Segmented({ label, value, options, surface = "app", onChange }: SegmentedProps) {
  return (
    <div className={cx("ds-seg", surface === "reader" && "ds-seg--reader")} role="radiogroup" aria-label={label}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={o.value === value}
          className={cx("ds-seg__btn", o.value === value && "ds-seg__btn--on")}
          onClick={() => onChange(o.value)}
        >
          {o.icon ? <Icon name={o.icon} size="sm" /> : null}
          {o.label}
        </button>
      ))}
    </div>
  );
}
