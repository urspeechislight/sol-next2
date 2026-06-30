import type { ReactNode } from "react";
import { cx } from "../../utils";
import { Icon } from "./Icon";
import type { IconName } from "../internal/icons";
import type { Surface } from "../surfaces";
import "./IconButton.css";

export type IconButtonSize = "sm" | "md";

export interface IconButtonProps {
  /** Accessible name (the button is icon/glyph-only). */
  label: string;
  /** Design-system icon to render. Omit and pass `children` for a text glyph. */
  icon?: IconName;
  size?: IconButtonSize;
  surface?: Surface;
  ariaPressed?: boolean;
  onClick?: () => void;
  /** Short text glyph (e.g. « » − +) when there is no icon for it. */
  children?: ReactNode;
}

/** A compact, square, icon-or-glyph-only button. The one source for the
    icon-button pattern the reader toolbar used to hand-roll. */
export function IconButton({
  label,
  icon,
  size = "md",
  surface = "app",
  ariaPressed,
  onClick,
  children,
}: IconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={ariaPressed}
      onClick={onClick}
      className={cx("ds-iconbtn", `ds-iconbtn--${surface}`, size === "sm" && "ds-iconbtn--sm")}
    >
      {icon ? <Icon name={icon} size="sm" /> : children}
    </button>
  );
}
