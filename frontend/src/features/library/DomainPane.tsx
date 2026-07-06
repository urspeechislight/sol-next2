import { Heading, Icon, Text } from '../../lib/design-system';
import type { Domain } from '../../lib/types';
import { FoundationalShelf } from './FoundationalShelf';
import { SchoolsSpread } from './SchoolsSpread';
import { sumCount } from '../../lib/taxonomy';
import { countLabel } from '../../lib/utils';
import { domainIcon, visibleCategories } from './lib';
import type { TraditionLens } from './lib';

export interface DomainPaneProps {
  domain: Domain;
  lens: TraditionLens;
  onPickCategory: (slug: string) => void;
  onOpen: (urn: string, page?: number) => void;
}

/** A chosen domain is a room, not a dump, and not the rail's index again:
    its blurb, the foundational shelf as a hand-turned spotlight, then the
    schools spread, every category as a section of its leading works. The
    rail carries the names and counts; this pane carries the books. */
export function DomainPane({ domain, lens, onPickCategory, onOpen }: DomainPaneProps) {
  const categories = visibleCategories(domain, lens);
  const tradition = lens === 'all' ? '' : lens;
  return (
    <section className="dpane">
      <header className="dpane__head">
        <Text size="xs" tone="faint" font="mono" className="works__crumb">
          Library / {domain.label}
        </Text>
        <span className="dpane__glyph">
          <Icon name={domainIcon(domain.id)} size="sm" />
        </span>
        <Heading level={2} font="arabic" dir="rtl">
          {domain.label_ar}
        </Heading>
        <Text as="p" size="sm" tone="muted">
          {domain.label} · {countLabel(sumCount(categories), 'work')} in{' '}
          {countLabel(categories.length, 'category', 'categories')}
        </Text>
        {domain.blurb ? (
          <Text as="p" size="md" tone="muted" className="dpane__blurb">
            {domain.blurb}
          </Text>
        ) : null}
      </header>
      <FoundationalShelf domain={domain.id} tradition={tradition} onOpen={onOpen} />
      <SchoolsSpread categories={categories} onPickCategory={onPickCategory} onOpen={onOpen} />
    </section>
  );
}
