import { Heading, Icon, Link, Text } from '../../lib/design-system';
import type { Domain } from '../../lib/types';
import { viewHref } from '../../lib/routes';
import { domainIcon, sumCount } from './lib';

interface DomainCardProps {
  domain: Domain;
  onPick: (id: string) => void;
}

function DomainCard({ domain, onPick }: DomainCardProps) {
  const count = sumCount(domain.categories);
  return (
    <Link
      href={viewHref('library')}
      className="ds-card ds-card--p-md ds-card--interactive dom-card"
      ariaLabel={`Browse ${domain.label}, ${count.toLocaleString()} works`}
      onActivate={() => onPick(domain.id)}
    >
      <span className="dom-card__glyph">
        <Icon name={domainIcon(domain.id)} size="sm" />
      </span>
      <span className="dom-card__ar" dir="rtl">
        {domain.label_ar}
      </span>
      <span className="dom-card__en">{domain.label}</span>
      <span className="dom-card__n">{count.toLocaleString()} works</span>
    </Link>
  );
}

export interface CorpusOverviewProps {
  domains: Domain[];
  onPickDomain: (id: string) => void;
}

/** The calm default right-pane state when nothing is selected: the corpus as a
    grid of illuminated domain cards that double as the start-here map. */
export function CorpusOverview({ domains, onPickDomain }: CorpusOverviewProps) {
  return (
    <section className="overview">
      <header className="overview__head">
        <Text size="xs" tone="accent" weight="semibold" className="overview__eyebrow">
          The Fihrist · الفِهرِست
        </Text>
        <Heading level={2}>Browse by domain</Heading>
        <Text as="p" size="md" tone="muted" className="overview__lede">
          The collection arranged in {domains.length} domains, read Arabic-first with English
          alongside. Choose one to begin, or open a category from the index.
        </Text>
      </header>
      <div className="overview__grid">
        {domains.map((d) => (
          <DomainCard key={d.id} domain={d} onPick={onPickDomain} />
        ))}
      </div>
    </section>
  );
}
