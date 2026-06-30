import { Heading, Text } from '../../lib/design-system';

import { ComponentsSection } from './ComponentsSection';
import { PrimitivesSection } from './PrimitivesSection';
import { TokensSection } from './TokensSection';
import './design.css';

/** The living styleguide at #/design: tokens, primitives, and reader components
    rendered from the real design system, never mocked. Reachable by URL; kept out
    of the nav bar on purpose. */
export function DesignSystemScreen() {
  return (
    <div className="ds-doc">
      <header className="ds-doc__lead">
        <Heading level={1}>Design system</Heading>
        <Text as="p" tone="muted">
          The single source of truth for every visual value and control. Everything below is
          rendered from the live design-system tokens, primitives, and components — not mockups.
        </Text>
      </header>
      <TokensSection />
      <PrimitivesSection />
      <ComponentsSection />
    </div>
  );
}
