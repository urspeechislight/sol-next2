import { Heading, Icon, Text, UnstyledButton } from '../../lib/design-system';
import type { Domain } from '../../lib/types';
import { domainIcon, sumCount, visibleCategories } from './lib';
import type { TraditionLens } from './lib';
import { RotationHero } from './RotationHero';

export interface DomainPaneProps {
  domain: Domain;
  lens: TraditionLens;
  onPickCategory: (slug: string) => void;
  onOpen: (urn: string) => void;
}

/** A chosen domain is a room, not a dump: its landmark rotation, its blurb,
    and its categories as tiles, each one step deeper. The flat all-works list
    is gone; full listings appear only once a category (or a search) narrows
    the scope to a readable shelf. */
export function DomainPane({ domain, lens, onPickCategory, onOpen }: DomainPaneProps) {
  const categories = visibleCategories(domain, lens);
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
          {domain.label} · {sumCount(categories).toLocaleString()} works in {categories.length}{' '}
          categories
        </Text>
        {domain.blurb ? (
          <Text as="p" size="md" tone="muted" className="dpane__blurb">
            {domain.blurb}
          </Text>
        ) : null}
      </header>
      <RotationHero domain={domain.id} onOpen={onOpen} />
      <div className="dpane__grid">
        {categories.map((c) => (
          <UnstyledButton
            key={c.slug}
            className="ds-card ds-card--p-md ds-card--interactive cat-card"
            onClick={() => onPickCategory(c.slug)}
            ariaLabel={`Browse ${c.label}, ${c.count.toLocaleString()} works`}
          >
            <span className="cat-card__ar" dir="rtl">
              {c.label_ar}
            </span>
            <span className="cat-card__en">{c.label}</span>
            <span className="cat-card__n">
              {c.count.toLocaleString()} works · {c.volume_count.toLocaleString()} volumes
            </span>
          </UnstyledButton>
        ))}
      </div>
    </section>
  );
}
