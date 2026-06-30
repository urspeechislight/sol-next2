import { Divider, Heading, Icon, Input, Link, Segmented, Text } from '../../lib/design-system';
import type { Domain } from '../../lib/types';
import { viewHref } from '../../lib/routes';
import { corpusTotals, domainIcon, sumCount, visibleCategories } from './lib';
import type { TraditionLens } from './lib';

const TRADITIONS = [
  { value: 'all', label: 'All' },
  { value: 'sunni', label: 'Sunni' },
  { value: 'shia', label: 'Shia' },
];

interface CategoryRowProps {
  slug: string;
  label: string;
  labelAr: string;
  count: number;
  active: boolean;
  onPick: (slug: string) => void;
}

function CategoryRow({ slug, label, labelAr, count, active, onPick }: CategoryRowProps) {
  return (
    <Link
      href={viewHref('library')}
      className={active ? 'fih-cat fih-cat--on' : 'fih-cat'}
      ariaCurrent={active}
      ariaLabel={`${label}, ${count.toLocaleString()} works`}
      onActivate={() => onPick(slug)}
    >
      <span className="fih-cat__en">{label}</span>
      <span className="fih-cat__ar" dir="rtl">
        {labelAr}
      </span>
      <span className="fih-cat__n">{count.toLocaleString()}</span>
    </Link>
  );
}

interface DomainGroupProps {
  domain: Domain;
  lens: TraditionLens;
  open: boolean;
  active: boolean;
  activeCat: string;
  onToggle: (id: string) => void;
  onPick: (slug: string) => void;
}

function DomainGroup({ domain, lens, open, active, activeCat, onToggle, onPick }: DomainGroupProps) {
  const cats = visibleCategories(domain, lens);
  if (cats.length === 0) return null;
  const count = sumCount(cats);
  const cls =
    'fih-dom__hd' + (open ? ' fih-dom__hd--open' : '') + (active ? ' fih-dom__hd--active' : '');
  return (
    <div className="fih-dom">
      <Link
        href={viewHref('library')}
        className={cls}
        ariaLabel={`${domain.label}, ${count.toLocaleString()} works`}
        onActivate={() => onToggle(domain.id)}
      >
        <Icon name={domainIcon(domain.id)} size="sm" />
        <span className="fih-dom__en">{domain.label}</span>
        <span className="fih-dom__ar" dir="rtl">
          {domain.label_ar}
        </span>
        <span className="fih-dom__n">{count.toLocaleString()}</span>
        <span className="fih-dom__chev">
          <Icon name="chevron-right" size="sm" />
        </span>
      </Link>
      {open ? (
        <div className="fih-dom__cats">
          {cats.map((c) => (
            <CategoryRow
              key={c.slug}
              slug={c.slug}
              label={c.label}
              labelAr={c.label_ar}
              count={c.count}
              active={c.slug === activeCat}
              onPick={onPick}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export interface FihristRailProps {
  domains: Domain[];
  lens: TraditionLens;
  filter: string;
  openDomains: Set<string>;
  activeCat: string;
  activeDomain: string;
  scoped: boolean;
  onLens: (lens: TraditionLens) => void;
  onFilter: (filter: string) => void;
  onToggleDomain: (id: string) => void;
  onPickCategory: (slug: string) => void;
  onReset: () => void;
}

/** The sticky catalogue rail: bilingual masthead, an index filter, the
    Sunni/Shia lens, and the seven domains as collapsed groups: the whole
    taxonomy in ~11 rows on landing, never the 39-chip wall. */
export function FihristRail({
  domains,
  lens,
  filter,
  openDomains,
  activeCat,
  activeDomain,
  scoped,
  onLens,
  onFilter,
  onToggleDomain,
  onPickCategory,
  onReset,
}: FihristRailProps) {
  const t = corpusTotals(domains);
  return (
    <aside className="fih-rail">
      <header className="fih-mast">
        <Heading level={2} font="arabic" dir="rtl">
          المكتبة
        </Heading>
        <Text size="xs" tone="accent" weight="semibold" className="fih-mast__eyebrow">
          The Library · الفِهرِست
        </Text>
        <Text as="p" size="xs" tone="faint" font="mono" className="fih-mast__stat">
          {t.works.toLocaleString()} works · {t.volumes.toLocaleString()} volumes · {t.domains}{' '}
          domains · {t.categories} categories
        </Text>
      </header>
      <div className="fih-controls">
        <Input
          value={filter}
          icon="search"
          type="search"
          ariaLabel="Search works"
          placeholder="Search works…"
          onInput={onFilter}
        />
        <Segmented
          label="Tradition"
          value={lens}
          options={TRADITIONS}
          onChange={(v) => onLens(v as TraditionLens)}
        />
      </div>
      <Divider />
      <Link
        href={viewHref('library')}
        className={scoped ? 'fih-all' : 'fih-all fih-all--on'}
        ariaCurrent={!scoped}
        onActivate={onReset}
      >
        <span>All works</span>
        <span className="fih-all__n">{t.works.toLocaleString()}</span>
      </Link>
      <nav className="fih-doms" aria-label="Domains">
        {domains.map((d) => (
          <DomainGroup
            key={d.id}
            domain={d}
            lens={lens}
            open={openDomains.has(d.id)}
            active={d.id === activeDomain}
            activeCat={activeCat}
            onToggle={onToggleDomain}
            onPick={onPickCategory}
          />
        ))}
      </nav>
    </aside>
  );
}
