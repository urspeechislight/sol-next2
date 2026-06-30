// Library helpers: the domain-glyph map, the tradition lens, label lookups, and
// the corpus/work formatting used by the Fihrist rail and the works pane. Kept
// here as single definitions so the rail, overview, and works pane never diverge.

import type { IconName } from '../../lib/design-system';
import type { Category, Domain, Tradition } from '../../lib/types';

export type TraditionLens = 'all' | 'sunni' | 'shia';

// Domain id -> a line glyph from the design-system icon set: a quiet per-domain
// illumination so the rail reads as a set of plates, not a flat list.
const DOMAIN_ICONS: Record<string, IconName> = {
  hadith: 'network',
  quran: 'book',
  fiqh: 'scroll',
  theology: 'star',
  biography: 'users',
  language: 'type',
  philosophy: 'compass',
  logic: 'compass',
  sciences: 'compass',
  ethics: 'sparkle',
  mysticism: 'sparkle',
  medicine: 'info',
  poetry: 'quote',
  devotional: 'star',
  history: 'globe',
};

export function domainIcon(id: string): IconName {
  return DOMAIN_ICONS[id] ?? 'layers';
}

/** A category is visible under a lens when the lens is All, the category matches
    the lens, or the category is shared/neutral (always visible under any lens). */
function inLens(tradition: Tradition, lens: TraditionLens): boolean {
  return lens === 'all' || tradition === lens || tradition === 'shared';
}

/** Categories of a domain visible under the tradition lens. The rail filter
    searches works (not the index), so it never narrows this tree. */
export function visibleCategories(domain: Domain, lens: TraditionLens): Category[] {
  return domain.categories.filter((c) => inLens(c.tradition, lens));
}

/** Sum of work counts across categories. */
export function sumCount(cats: { count: number }[]): number {
  return cats.reduce((n, c) => n + c.count, 0);
}

function find(domains: Domain[], slug: string): Category | null {
  for (const d of domains) for (const c of d.categories) if (c.slug === slug) return c;
  return null;
}

export function labelOf(domains: Domain[], slug: string): string {
  return find(domains, slug)?.label ?? slug;
}

export function labelArOf(domains: Domain[], slug: string): string {
  return find(domains, slug)?.label_ar ?? slug;
}

export function domainLabel(domains: Domain[], id: string): string {
  return domains.find((d) => d.id === id)?.label ?? id;
}

export function domainLabelAr(domains: Domain[], id: string): string {
  return domains.find((d) => d.id === id)?.label_ar ?? id;
}

/** Corpus totals for the rail masthead. */
export function corpusTotals(domains: Domain[]): {
  works: number;
  volumes: number;
  categories: number;
  domains: number;
} {
  let works = 0;
  let volumes = 0;
  let categories = 0;
  for (const d of domains)
    for (const c of d.categories) {
      works += c.count;
      volumes += c.volume_count;
      categories += 1;
    }
  return { works, volumes, categories, domains: domains.length };
}
