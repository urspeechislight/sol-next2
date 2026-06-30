import type { ReactNode } from "react";
import { cx } from "../../utils";
import "./Card.css";

export type CardVariant = "flat" | "raised" | "sunken";
export type CardPad = "none" | "sm" | "md" | "lg";

const VARIANT_CLASS: Record<CardVariant, string> = {
  flat: "ds-card--flat", raised: "ds-card--raised", sunken: "ds-card--sunken",
};
const PAD_CLASS: Record<CardPad, string> = {
  none: "ds-card--p-none", sm: "ds-card--p-sm", md: "ds-card--p-md", lg: "ds-card--p-lg",
};

export interface CardProps {
  variant?: CardVariant;
  pad?: CardPad;
  interactive?: boolean;
  as?: "div" | "article" | "section" | "li";
  className?: string;
  children: ReactNode;
}

export function Card({
  variant = "flat",
  pad = "md",
  interactive = false,
  as: Tag = "div",
  className,
  children,
}: CardProps) {
  return (
    <Tag
      className={cx(
        "ds-card",
        VARIANT_CLASS[variant],
        PAD_CLASS[pad],
        interactive && "ds-card--interactive",
        className,
      )}
    >
      {children}
    </Tag>
  );
}
