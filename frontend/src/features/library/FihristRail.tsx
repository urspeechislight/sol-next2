import {
  Divider,
  Heading,
  Icon,
  Input,
  Link,
  Segmented,
  Text,
  UnstyledButton,
} from '../../lib/design-system';
import type { Domain } from '../../lib/types';
import { viewHref } from '../../lib/routes';
import { corpusTotals, sumCount } from '../../lib/taxonomy';
import { formatCount } from '../../lib/utils';
import { traditionLabel } from '../narrators/labels';
import { domainIcon, visibleCategories } from './lib';
import type { TraditionLens } from './lib';

const TRADITIONS = [
  { value: 'all', label: 'All' },
  { value: 'sunni', label: traditionLabel('sunni') },
  { value: 'shia', label: traditionLabel('shia') },
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
      ariaLabel={`${label}, ${formatCount(count)} works`}
      onActivate={() => onPick(slug)}
    >
      <span className="fih-cat__en">{label}</span>
      <span className="fih-cat__ar" dir="rtl">
        {labelAr}
      </span>
      <span className="fih-cat__n">{formatCount(count)}</span>
    </Link>
  );
}

interface DomainGroupProps {
  domain: Domain;
  lens: TraditionLens;
  open: boolean;
  active: boolean;
  activeCat: string;
  onSelect: (id: string) => void;
  onToggle: (id: string) => void;
  onPick: (slug: string) => void;
}

/** One rail group with one consequence per control: the domain's name row
    selects it (the pane opens its room), the chevron alone folds the
    category list open or closed. */
function DomainGroup({
  domain,
  lens,
  open,
  active,
  activeCat,
  onSelect,
  onToggle,
  onPick,
}: DomainGroupProps) {
  const cats = visibleCategories(domain, lens);
  if (cats.length === 0) return null;
  const count = sumCount(cats);
  const cls =
    'fih-dom__hd' + (open ? ' fih-dom__hd--open' : '') + (active ? ' fih-dom__hd--active' : '');
  return (
    <div className="fih-dom">
      <div className={cls}>
        <Link
          href={viewHref('library')}
          className="fih-dom__sel"
          ariaCurrent={active}
          ariaLabel={`${domain.label}, ${formatCount(count)} works`}
          onActivate={() => onSelect(domain.id)}
        >
          <Icon name={domainIcon(domain.id)} size="sm" />
          <span className="fih-dom__en">{domain.label}</span>
          <span className="fih-dom__ar" dir="rtl">
            {domain.label_ar}
          </span>
          <span className="fih-dom__n">{formatCount(count)}</span>
        </Link>
        <UnstyledButton
          className="fih-dom__chev"
          onClick={() => onToggle(domain.id)}
          ariaPressed={open}
          ariaLabel={`${open ? 'Collapse' : 'Expand'} ${domain.label} categories`}
        >
          <Icon name="chevron-right" size="sm" />
        </UnstyledButton>
      </div>
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
  onSelectDomain: (id: string) => void;
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
  onSelectDomain,
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
          {formatCount(t.works)} works · {formatCount(t.volumes)} volumes · {t.domains} domains ·{' '}
          {t.categories} categories
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
        <span className="fih-all__n">{formatCount(t.works)}</span>
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
            onSelect={onSelectDomain}
            onToggle={onToggleDomain}
            onPick={onPickCategory}
          />
        ))}
      </nav>
    </aside>
  );
}
