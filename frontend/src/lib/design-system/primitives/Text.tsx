import type { ElementType, ReactNode } from 'react';
import { cx } from '../../utils';
import './Text.css';

export type TextSize = 'xs' | 'sm' | 'base' | 'md' | 'lg' | 'xl';
export type TextTone = 'default' | 'muted' | 'faint' | 'ghost' | 'accent' | 'danger';
export type TextWeight = 'regular' | 'medium' | 'semibold';
export type TextFont = 'sans' | 'serif' | 'mono' | 'arabic';

export interface TextProps {
  as?: ElementType;
  size?: TextSize;
  tone?: TextTone;
  weight?: TextWeight;
  font?: TextFont;
  numeric?: boolean;
  dir?: 'rtl' | 'ltr';
  id?: string;
  className?: string;
  children: ReactNode;
}

/** Orthogonal text primitive: size x tone x weight x font, matching Text.css. */
export function Text({
  as: Tag = 'span',
  size = 'base',
  tone = 'default',
  weight,
  font,
  numeric,
  dir,
  id,
  className,
  children,
}: TextProps) {
  return (
    <Tag
      id={id}
      dir={dir}
      className={cx(
        'ds-text',
        `ds-text--${size}`,
        `ds-text--tone-${tone}`,
        weight && `ds-text--w-${weight}`,
        font && `ds-text--f-${font}`,
        numeric && 'ds-text--numeric',
        className,
      )}
    >
      {children}
    </Tag>
  );
}
