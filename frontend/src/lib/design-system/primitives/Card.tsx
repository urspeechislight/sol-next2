import type { ReactNode } from 'react';
import { cx } from '../../utils';
import './Card.css';

export type CardVariant = 'flat' | 'raised';

const VARIANT_CLASS: Record<CardVariant, string> = {
  flat: 'ds-card--flat',
  raised: 'ds-card--raised',
};

export interface CardProps {
  variant?: CardVariant;
  interactive?: boolean;
  as?: 'div' | 'article' | 'section' | 'li';
  className?: string;
  children: ReactNode;
}

export function Card({
  variant = 'flat',
  interactive = false,
  as: Tag = 'div',
  className,
  children,
}: CardProps) {
  return (
    <Tag
      className={cx(
        'ds-card',
        VARIANT_CLASS[variant],
        interactive && 'ds-card--interactive',
        className,
      )}
    >
      {children}
    </Tag>
  );
}
