import type { ReactNode } from "react";
import { cx } from "../../utils";
import { ALIGN_CLASS, JUSTIFY_CLASS, type Gap, type Justify } from "./Stack";
import "./Stack.css";

export type InlineAlign = "start" | "center" | "end" | "baseline" | "stretch";

export interface InlineProps {
  gap?: Gap;
  align?: InlineAlign;
  justify?: Justify;
  wrap?: boolean;
  as?: "div" | "nav" | "ul" | "header" | "footer";
  className?: string;
  children: ReactNode;
}

export function Inline({ gap = 2, align = "center", justify = "start", wrap = true, as: Tag = "div", className, children }: InlineProps) {
  return (
    <Tag
      className={cx("ds-inline", `ds-gap-${gap}`, ALIGN_CLASS[align], JUSTIFY_CLASS[justify],
        wrap ? "ds-inline--wrap" : "ds-inline--nowrap", className)}
    >
      {children}
    </Tag>
  );
}
