import type { ReactNode } from "react";
import { cx } from "../../utils";
import "./Stack.css";

export type Gap = "none" | "xs" | "sm" | "md" | "lg" | "xl";
export type Align = "start" | "center" | "end" | "stretch";
export type Justify = "start" | "center" | "end" | "between";

export const GAP_CLASS: Record<Gap, string> = {
  none: "ds-gap-none", xs: "ds-gap-xs", sm: "ds-gap-sm", md: "ds-gap-md", lg: "ds-gap-lg", xl: "ds-gap-xl",
};
export const ALIGN_CLASS: Record<Align, string> = {
  start: "ds-align-start", center: "ds-align-center", end: "ds-align-end", stretch: "ds-align-stretch",
};
export const JUSTIFY_CLASS: Record<Justify, string> = {
  start: "ds-justify-start", center: "ds-justify-center", end: "ds-justify-end", between: "ds-justify-between",
};

export interface StackProps {
  gap?: Gap;
  align?: Align;
  justify?: Justify;
  as?: "div" | "section" | "ul" | "nav" | "li";
  className?: string;
  children: ReactNode;
}

export function Stack({ gap = "md", align = "stretch", justify = "start", as: Tag = "div", className, children }: StackProps) {
  return (
    <Tag className={cx("ds-stack", GAP_CLASS[gap], ALIGN_CLASS[align], JUSTIFY_CLASS[justify], className)}>
      {children}
    </Tag>
  );
}
