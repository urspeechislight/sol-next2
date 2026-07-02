import type { ReactNode } from 'react';
import { cx } from '../../utils';
import './Heading.css';

export type HeadingLevel = 1 | 2 | 3 | 4;
export type HeadingFont = 'serif' | 'sans' | 'arabic';

const LEVEL_TAG = { 1: 'h1', 2: 'h2', 3: 'h3', 4: 'h4' } as const;

export interface HeadingProps {
  level: HeadingLevel;
  font?: HeadingFont;
  dir?: 'rtl' | 'ltr';
  id?: string;
  className?: string;
  children: ReactNode;
}

export function Heading({ level, font = 'serif', dir, id, className, children }: HeadingProps) {
  const Tag = LEVEL_TAG[level];
  return (
    <Tag
      id={id}
      dir={dir}
      className={cx('ds-heading', `ds-heading--${level}`, `ds-heading--${font}`, className)}
    >
      {children}
    </Tag>
  );
}
