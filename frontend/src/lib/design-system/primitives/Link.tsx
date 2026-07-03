import type { MouseEvent, ReactNode } from 'react';
import { cx } from '../../utils';
import './Link.css';

export type LinkVariant = 'default' | 'quiet' | 'accent';

const VARIANT_CLASS: Record<LinkVariant, string> = {
  default: 'ds-link--default',
  quiet: 'ds-link--quiet',
  accent: 'ds-link--accent',
};

export interface LinkProps {
  href: string;
  variant?: LinkVariant;
  ariaLabel?: string;
  ariaCurrent?: boolean;
  dir?: 'rtl' | 'ltr';
  className?: string;
  /** Client-side intercept for a plain, primary-button click; the real href
      stays live underneath, so ctrl/cmd/middle-click and "open in a new tab"
      still work exactly like a normal link instead of being swallowed by the
      SPA navigation. */
  onActivate?: () => void;
  children: ReactNode;
}

export function Link({
  href,
  variant = 'default',
  ariaLabel,
  ariaCurrent,
  dir,
  className,
  onActivate,
  children,
}: LinkProps) {
  const onClick = onActivate
    ? (e: MouseEvent<HTMLAnchorElement>) => {
        const modified = e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey;
        if (e.defaultPrevented || modified) return;
        e.preventDefault();
        onActivate();
      }
    : undefined;
  return (
    <a
      href={href}
      dir={dir}
      aria-label={ariaLabel}
      aria-current={ariaCurrent ? 'page' : undefined}
      onClick={onClick}
      className={cx('ds-link', VARIANT_CLASS[variant], className)}
    >
      {children}
    </a>
  );
}
