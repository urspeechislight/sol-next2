import type { ReactNode } from "react";
import { cx } from "../../utils";
import { GAP_CLASS, ALIGN_CLASS, JUSTIFY_CLASS, type Gap, type Align, type Justify } from "./Stack";
import "./Stack.css";
import "./Inline.css";

export interface InlineProps {
  gap?: Gap;
  align?: Align;
  justify?: Justify;
  wrap?: boolean;
  as?: "div" | "nav" | "ul" | "header" | "footer";
  className?: string;
  children: ReactNode;
}

/** Horizontal cluster: reuses Stack's gap/align/justify scale on a flex row. */
export function Inline({ gap = "sm", align = "center", justify = "start", wrap = true, as: Tag = "div", className, children }: InlineProps) {
  return (
    <Tag
      className={cx(
        "ds-inline",
        GAP_CLASS[gap],
        ALIGN_CLASS[align],
        JUSTIFY_CLASS[justify],
        wrap ? "ds-inline--wrap" : "ds-inline--nowrap",
        className,
      )}
    >
      {children}
    </Tag>
  );
}
