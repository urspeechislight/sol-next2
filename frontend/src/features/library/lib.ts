// Library helpers: the domain-glyph map, the tradition lens, label lookups, and
// the era/edition folding shared by the Fihrist rail, the panes, and the shelf.
// Kept here as single definitions so the rail, overview, and works pane never
// diverge.

import type { IconName } from '../../lib/design-system';
import type { Category, Domain, Tradition, Work } from '../../lib/types';

export type TraditionLens = 'all' | 'sunni' | 'shia';

// Hijri centuries as explicit bilingual labels (the corpus spans 1st-15th);
// index 0 is the undated bucket. Table-driven like the surah names: no
// ordinal arithmetic, no untranslatable strings.
const CENTURY_LABELS: readonly { en: string; ar: string }[] = [
  { en: 'Undated', ar: 'بدون تاريخ' },
  { en: '1st century AH', ar: 'القرن الأول' },
  { en: '2nd century AH', ar: 'القرن الثاني' },
  { en: '3rd century AH', ar: 'القرن الثالث' },
  { en: '4th century AH', ar: 'القرن الرابع' },
  { en: '5th century AH', ar: 'القرن الخامس' },
  { en: '6th century AH', ar: 'القرن السادس' },
  { en: '7th century AH', ar: 'القرن السابع' },
  { en: '8th century AH', ar: 'القرن الثامن' },
  { en: '9th century AH', ar: 'القرن التاسع' },
  { en: '10th century AH', ar: 'القرن العاشر' },
  { en: '11th century AH', ar: 'القرن الحادي عشر' },
  { en: '12th century AH', ar: 'القرن الثاني عشر' },
  { en: '13th century AH', ar: 'القرن الثالث عشر' },
  { en: '14th century AH', ar: 'القرن الرابع عشر' },
  { en: '15th century AH', ar: 'القرن الخامس عشر' },
];

const YEARS_PER_CENTURY = 100;

export interface EraGroup {
  century: number;
  labelEn: string;
  labelAr: string;
  works: Work[];
}

/** The Hijri century of a work's author (0 = undated / out of table range). */
export function centuryOf(work: Work): number {
  const death = work.death_year_ah;
  if (!death) return 0;
  const century = Math.floor((death - 1) / YEARS_PER_CENTURY) + 1;
  return century < CENTURY_LABELS.length ? century : 0;
}

/** Group a scope's works into Hijri-century sections, each sorted by death
    year then title, dated eras first and the undated bucket last. */
export function groupByEra(works: Work[]): EraGroup[] {
  const buckets = new Map<number, Work[]>();
  for (const w of works) {
    const c = centuryOf(w);
    const bucket = buckets.get(c);
    if (bucket) bucket.push(w);
    else buckets.set(c, [w]);
  }
  const order = [...buckets.keys()].sort((a, b) => {
    if (a === 0) return 1;
    if (b === 0) return -1;
    return a - b;
  });
  return order.map((century) => {
    const group = buckets.get(century) ?? [];
    group.sort(
      (a, b) =>
        (a.death_year_ah ?? Number.MAX_SAFE_INTEGER) -
          (b.death_year_ah ?? Number.MAX_SAFE_INTEGER) ||
        (a.title_en ?? a.title_ar).localeCompare(b.title_en ?? b.title_ar),
    );
    const label = CENTURY_LABELS[century];
    return { century, labelEn: label.en, labelAr: label.ar, works: group };
  });
}

/** One entry per title+author: editions and translations collapse to the
    first occurrence, preserving order. */
export function dedupeEditions(works: Work[]): Work[] {
  const seen = new Set<string>();
  const out: Work[] = [];
  for (const w of works) {
    const key = `${w.title_en ?? w.title_ar}|${w.author ?? ''}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(w);
  }
  return out;
}

/** Case-insensitive author match across both name fields, for the author
    filter: a substring so partial names ("tusi") reach their variants. */
export function matchesAuthor(work: Work, needle: string): boolean {
  const low = needle.trim().toLowerCase();
  if (!low) return true;
  return (work.author ?? '').toLowerCase().includes(low) || (work.author_ar ?? '').includes(needle);
}

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

/** A localized count with its correctly pluralized noun: "1 work", "18 works",
    "1 category", "12 categories". The single grammar for every count label the
    library prints, so "1 works" can never appear. */
export function countLabel(n: number, singular: string, plural = `${singular}s`): string {
  return `${n.toLocaleString()} ${n === 1 ? singular : plural}`;
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
