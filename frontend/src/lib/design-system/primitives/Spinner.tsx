import { cx } from '../../utils';
import './Spinner.css';

export type SpinnerSize = 'sm' | 'md';

const SIZE_CLASS: Record<SpinnerSize, string> = {
  sm: 'ds-spinner--sm',
  md: 'ds-spinner--md',
};

export interface SpinnerProps {
  size?: SpinnerSize;
  label?: string;
  className?: string;
}

export function Spinner({ size = 'md', label = 'Loading', className }: SpinnerProps) {
  return (
    <span
      role="status"
      aria-label={label}
      className={cx('ds-spinner', SIZE_CLASS[size], className)}
    />
  );
}
