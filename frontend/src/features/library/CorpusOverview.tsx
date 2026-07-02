import { Heading, IndexRow, Text } from '../../lib/design-system';
import type { Domain } from '../../lib/types';
import { Apparatus } from './Apparatus';
import { countLabel, sumCount, visibleCategories } from './lib';
import type { TraditionLens } from './lib';

export interface CorpusOverviewProps {
  domains: Domain[];
  lens: TraditionLens;
  onPickDomain: (id: string) => void;
}

/** The calm default right-pane state when nothing is selected: the domains as
    contents rows, the same fihrist grammar as the landing page, so arriving
    here reads as turning the page, not changing products. Counts honor the
    tradition lens exactly as the rail's do, so the two surfaces can never
    state different totals for the same domain. The foundational shelf appears
    one level down (domain and category rooms), where the corpus's
    canonical-rank data makes a coherent claim; at corpus level it surfaces
    mis-ranked outliers, so no shelf is shown rather than a wrong one. */
export function CorpusOverview({ domains, lens, onPickDomain }: CorpusOverviewProps) {
  const rows = domains
    .map((d) => ({ domain: d, cats: visibleCategories(d, lens) }))
    .filter((r) => r.cats.length > 0);
  return (
    <section className="overview">
      <header className="overview__head">
        <Text size="xs" tone="accent" weight="semibold" className="overview__eyebrow">
          The Fihrist · الفِهرِست
        </Text>
        <Heading level={2}>Browse by domain</Heading>
        <Text as="p" size="md" tone="muted" className="overview__lede">
          The collection arranged in {rows.length} domains, read Arabic-first with English
          alongside. Choose one to begin, or open a category from the index.
        </Text>
      </header>
      <div className="overview__contents">
        <Apparatus marginalia={`${rows.length}`}>Domains · المجالات</Apparatus>
        <ol className="overview__rows">
          {rows.map(({ domain: d, cats }) => (
            <li key={d.id} className="overview__row">
              <IndexRow
                en={d.label}
                ar={d.label_ar}
                blurb={d.blurb}
                meta={countLabel(sumCount(cats), 'work')}
                onActivate={() => onPickDomain(d.id)}
                ariaLabel={`Browse ${d.label}, ${countLabel(sumCount(cats), 'work')}`}
              />
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
