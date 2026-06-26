import type { ReactNode } from "react";
import { cx } from "../../utils";
import "./Stack.css";

export type Gap = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
export type Align = "start" | "center" | "end" | "stretch";
export type Justify = "start" | "center" | "end" | "between";

export const ALIGN_CLASS: Record<string, string> = {
  start: "ds-align-start", center: "ds-align-center", end: "ds-align-end",
  stretch: "ds-align-stretch", baseline: "ds-align-baseline",
};
export const JUSTIFY_CLASS: Record<Justify, string> = {
  start: "ds-justify-start", center: "ds-justify-center",
  end: "ds-justify-end", between: "ds-justify-between",
};

export interface StackProps {
  gap?: Gap;
  align?: Align;
  justify?: Justify;
  as?: "div" | "section" | "ul" | "nav" | "li";
  className?: string;
  children: ReactNode;
}

export function Stack({ gap = 4, align = "stretch", justify = "start", as: Tag = "div", className, children }: StackProps) {
  return (
    <Tag
      className={cx("ds-stack", `ds-gap-${gap}`, ALIGN_CLASS[align], JUSTIFY_CLASS[justify], className)}
    >
      {children}
    </Tag>
  );
}
