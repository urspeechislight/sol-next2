import { cx } from "../../utils";
import "./Divider.css";

export interface DividerProps {
  orientation?: "horizontal" | "vertical";
  className?: string;
}

export function Divider({ orientation = "horizontal", className }: DividerProps) {
  return (
    <hr
      aria-orientation={orientation}
      className={cx("ds-divider", `ds-divider--${orientation}`, className)}
    />
  );
}
