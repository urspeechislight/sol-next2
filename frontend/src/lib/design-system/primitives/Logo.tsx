import { cx } from '../../utils';
import { ASSETS } from '../../routes';
import type { IconSize } from './Icon';
import './Logo.css';

export type LogoSize = IconSize;

const SIZE_CLASS: Record<LogoSize, string> = {
  sm: 'ds-logo--sm',
  md: 'ds-logo--md',
  lg: 'ds-logo--lg',
  xl: 'ds-logo--xl',
};

export interface LogoProps {
  size?: LogoSize;
  wordmark?: boolean;
  className?: string;
  title?: string;
}

/** The SOL brand: the gold Karbalāʾ shrine mark (a transparent PNG that reads
    on light and dark grounds) with an optional wordmark. The image asset is the
    single source of truth:never redraw it. Lives at ASSETS.LOGO_MARK. */
export function Logo({ size = 'md', wordmark = true, className, title = 'SOL' }: LogoProps) {
  return (
    <span className={cx('ds-logo', SIZE_CLASS[size], className)} role="img" aria-label={title}>
      <img className="ds-logo__mark" src={ASSETS.LOGO_MARK} alt="" aria-hidden="true" />
      {wordmark ? <span className="ds-logo__word">SOL</span> : null}
    </span>
  );
}
