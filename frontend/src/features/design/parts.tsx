import type { ReactNode } from 'react';

import { Heading, Text } from '../../lib/design-system';
import { cssVar } from './css-var';
import './design.css';

export function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="ds-doc__section" id={id}>
      <Heading level={2}>{title}</Heading>
      {children}
    </section>
  );
}

export function Spec({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="ds-doc__spec">
      <Text as="p" size="xs" tone="faint" font="mono">
        {label}
      </Text>
      <div className="ds-doc__demo">{children}</div>
    </div>
  );
}

export function Swatch({ name, token }: { name: string; token: string }) {
  return (
    <div className="ds-doc__swatch">
      <span className="ds-doc__chip" style={cssVar('--chip', token)} />
      <Text as="span" size="xs" font="mono" tone="muted">
        {name}
      </Text>
    </div>
  );
}
