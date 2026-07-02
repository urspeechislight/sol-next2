// passages.ts: pure helpers for the content scope's work-grouped hit stream.
// The corpus endpoint orders hits category -> book -> volume -> page, so hits
// for one work arrive adjacent and grouping is a single pass over the loaded
// window; grouping always runs over the FULL accumulated list, so a work
// split across a load-more boundary merges instead of repeating its head.

import type { CorpusMatch } from '../../lib/types';

export interface PassageGroup {
  /** Stable render key: the work's stored Arabic title + author. */
  key: string;
  title_ar: string;
  title_en: string | null;
  author: string | null;
  category: string;
  hits: CorpusMatch[];
}

/** Group adjacent hits belonging to one work (same stored Arabic title +
    author; volume URNs differ per volume, so the URN cannot be the key). */
export function groupByWork(items: readonly CorpusMatch[]): PassageGroup[] {
  const groups: PassageGroup[] = [];
  for (const m of items) {
    const key = `${m.title_ar}|${m.author ?? ''}`;
    const last = groups[groups.length - 1];
    if (last && last.key === key) {
      last.hits.push(m);
      continue;
    }
    groups.push({
      key,
      title_ar: m.title_ar,
      title_en: m.title_en,
      author: m.author,
      category: m.category,
      hits: [m],
    });
  }
  return groups;
}

/** The compact reference a passage row carries in its mono margin. */
export function refLabel(m: CorpusMatch): string {
  return m.volume ? `vol. ${m.volume} · p. ${m.page}` : `p. ${m.page}`;
}
