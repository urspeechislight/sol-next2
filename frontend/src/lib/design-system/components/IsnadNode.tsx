import { cx } from '../../utils';
import { Badge } from '../primitives/Badge';
import type { BadgeVariant } from '../primitives/Badge';
import './IsnadNode.css';

export type IsnadNodeVariant = 'tree' | 'flow' | 'card';

export interface IsnadNodeProps {
  /** Layout: 'tree' rows with connectors, 'flow' compact pills, 'card' framed. */
  variant?: IsnadNodeVariant;
  /** Position in the chain; 0 is the origin (shown as a star). */
  index: number;
  /** Draw the connector down to the next node. */
  showLine?: boolean;
  nameEn: string;
  nameAr: string;
  died?: string | number | null;
  role: string;
  /** Reliability label to show as a grade badge (omit to hide it). */
  grade?: string | null;
  /** Tone for the grade badge; the caller maps the grade via variants.ts. */
  gradeVariant?: BadgeVariant;
  onClick?: () => void;
}

/** One node of an isnād transmission chain: dot, narrator, optional grade. */
export function IsnadNode({
  variant = 'tree',
  index,
  showLine,
  nameEn,
  nameAr,
  died,
  role,
  grade,
  gradeVariant = 'default',
  onClick,
}: IsnadNodeProps) {
  const origin = index === 0;
  return (
    <button
      type="button"
      className={cx('ds-isnad-node', variant !== 'tree' && `ds-isnad-node--${variant}`)}
      onClick={onClick}
    >
      {showLine ? <span className="ds-isnad-node__line" /> : null}
      <span className={cx('ds-isnad-node__dot', origin && 'ds-isnad-node__dot--origin')}>
        {origin ? '★' : index}
      </span>
      <div className="ds-isnad-node__body">
        <p className="ds-isnad-node__en">{nameEn}</p>
        {variant !== 'flow' ? (
          <p className="ds-isnad-node__meta">
            {died ? `d. ${died}` : '—'} · {role}
          </p>
        ) : null}
        {variant !== 'flow' && grade ? (
          <Badge surface="reader" variant={gradeVariant}>
            {grade}
          </Badge>
        ) : null}
      </div>
      <p className="ds-isnad-node__ar" dir="rtl">
        {nameAr}
      </p>
    </button>
  );
}
