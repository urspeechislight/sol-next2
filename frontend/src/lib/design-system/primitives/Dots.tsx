import { cx } from '../../utils';
import { UnstyledButton } from './UnstyledButton';
import './Dots.css';

export interface DotsProps {
  count: number;
  active: number;
  /** Accessible name for dot i, e.g. the title it reveals. */
  labelFor: (index: number) => string;
  onPick: (index: number) => void;
}

/** Rotation-position dots: the one indicator for anything that cycles
    (tafsīr excerpts, the landmark rotation). One definition of the dot's
    size, colour, and active state. */
export function Dots({ count, active, labelFor, onPick }: DotsProps) {
  return (
    <span className="ds-dots">
      {Array.from({ length: count }).map((_, i) => (
        <UnstyledButton
          key={i}
          className={cx('ds-dots__dot', i === active && 'ds-dots__dot--active')}
          ariaLabel={labelFor(i)}
          onClick={() => onPick(i)}
        />
      ))}
    </span>
  );
}
