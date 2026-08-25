import { ICON_PATHS, type IconName } from '../internal/icons';
import { cx } from '../../utils';
import './Icon.css';

export type IconSize = 'sm' | 'md' | 'lg' | 'xl';

const SIZE_CLASS: Record<IconSize, string> = {
  sm: 'ds-icon--sm',
  md: 'ds-icon--md',
  lg: 'ds-icon--lg',
  xl: 'ds-icon--xl',
};

export interface IconProps {
  name: IconName;
  size?: IconSize;
  className?: string;
  title?: string;
}

export function Icon({ name, size = 'md', className, title }: IconProps) {
  const segments = ICON_PATHS[name].split('M').filter(Boolean);
  return (
    <svg
      viewBox="0 0 24 24"
      className={cx('ds-icon', SIZE_CLASS[size], className)}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      {title ? <title>{title}</title> : null}
      {segments.map((seg, i) => (
        <path key={i} d={`M${seg}`} />
      ))}
    </svg>
  );
}
