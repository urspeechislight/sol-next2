import type { ReactNode } from 'react';
import { Text, type TextWeight } from './Text';

export type HeadingLevel = 1 | 2 | 3;

const LEVEL_AS = { 1: 'h1', 2: 'h2', 3: 'h3' } as const;

export interface HeadingProps {
  level: HeadingLevel;
  weight?: TextWeight;
  dir?: 'rtl' | 'ltr';
  className?: string;
  id?: string;
  children: ReactNode;
}

/** Heading delegates to Text's `as=` (no independent styling). */
export function Heading({ level, weight, dir, className, id, children }: HeadingProps) {
  return (
    <Text as={LEVEL_AS[level]} weight={weight} dir={dir} className={className} id={id}>
      {children}
    </Text>
  );
}
