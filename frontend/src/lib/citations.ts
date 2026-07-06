import type { QuranCitation } from './types';

/** A page's Arabic text split at citation boundaries: a ``cite`` segment keeps
    the printed reference glyphs in ``value`` (never rewritten) and carries the
    resolved verse; ``text`` segments are everything between. Concatenating every
    segment's ``value`` reproduces the input exactly. */
export type CiteSegment =
  | { type: 'text'; value: string }
  | { type: 'cite'; value: string; surah: number; ayaStart: number; ayaEnd: number };

/** Split ``text`` at the citation ranges (offset + length into the same source
    string the sidecar was built from), wrapping each in a ``cite`` segment.
    Citations are sorted by offset; any that overlaps a prior one or runs past
    the end of ``text`` is skipped, so a stale anchor can never corrupt the
    render. Pure. */
export function citationSegments(text: string, cites: readonly QuranCitation[]): CiteSegment[] {
  if (!text) return [];
  if (cites.length === 0) return [{ type: 'text', value: text }];
  const sorted = [...cites].sort((a, b) => a.offset - b.offset);
  const segments: CiteSegment[] = [];
  let cursor = 0;
  for (const c of sorted) {
    if (c.offset < cursor || c.offset + c.length > text.length) continue;
    if (c.offset > cursor) segments.push({ type: 'text', value: text.slice(cursor, c.offset) });
    segments.push({
      type: 'cite',
      value: text.slice(c.offset, c.offset + c.length),
      surah: c.surah,
      ayaStart: c.aya_start,
      ayaEnd: c.aya_end,
    });
    cursor = c.offset + c.length;
  }
  if (cursor < text.length) segments.push({ type: 'text', value: text.slice(cursor) });
  return segments;
}
