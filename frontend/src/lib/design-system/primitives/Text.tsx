import type { ElementType, ReactNode } from "react";
import { cx } from "../../utils";
import "./Text.css";

export type TextAs = "h1" | "h2" | "h3" | "body" | "muted" | "arabic";
export type TextWeight = "regular" | "medium" | "bold";

const AS_TAG: Record<TextAs, ElementType> = {
  h1: "h1", h2: "h2", h3: "h3", body: "p", muted: "p", arabic: "p",
};
const AS_CLASS: Record<TextAs, string> = {
  h1: "ds-text--h1", h2: "ds-text--h2", h3: "ds-text--h3",
  body: "ds-text--body", muted: "ds-text--muted", arabic: "ds-text--arabic",
};
const WEIGHT_CLASS: Record<TextWeight, string> = {
  regular: "ds-text--w-regular", medium: "ds-text--w-medium", bold: "ds-text--w-bold",
};

export interface TextProps {
  as?: TextAs;
  weight?: TextWeight;
  dir?: "rtl" | "ltr";
  className?: string;
  id?: string;
  children: ReactNode;
}

export function Text({ as = "body", weight, dir, className, id, children }: TextProps) {
  const Tag = AS_TAG[as];
  return (
    <Tag id={id} dir={dir} className={cx("ds-text", AS_CLASS[as], weight && WEIGHT_CLASS[weight], className)}>
      {children}
    </Tag>
  );
}
