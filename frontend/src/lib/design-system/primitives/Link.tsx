import type { ReactNode } from "react";
import { cx } from "../../utils";
import "./Link.css";

export type LinkVariant = "default" | "quiet" | "accent";

const VARIANT_CLASS: Record<LinkVariant, string> = {
  default: "ds-link--default",
  quiet: "ds-link--quiet",
  accent: "ds-link--accent",
};

export interface LinkProps {
  href: string;
  variant?: LinkVariant;
  external?: boolean;
  ariaLabel?: string;
  ariaCurrent?: boolean;
  dir?: "rtl" | "ltr";
  className?: string;
  /** Client-side intercept; real href stays for deep-linking / SSR. */
  onActivate?: () => void;
  children: ReactNode;
}

export function Link({
  href, variant = "default", external = false, ariaLabel, ariaCurrent,
  dir, className, onActivate, children,
}: LinkProps) {
  const onClick = onActivate
    ? (e: { preventDefault: () => void }) => { e.preventDefault(); onActivate(); }
    : undefined;
  return (
    <a
      href={href}
      dir={dir}
      aria-label={ariaLabel}
      aria-current={ariaCurrent ? "page" : undefined}
      target={external ? "_blank" : undefined}
      rel={external ? "noreferrer noopener" : undefined}
      onClick={onClick}
      className={cx("ds-link", VARIANT_CLASS[variant], className)}
    >
      {children}
    </a>
  );
}
