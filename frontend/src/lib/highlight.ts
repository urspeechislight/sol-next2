// highlight.ts:fold-aware substring highlighting for search results. Splits a
// string into match / non-match segments using the SEARCH fold from
// lib/arabic.ts (foldSearch), the SAME fold the corpus index + query use, so
// every span flagged here is one the corpus actually matched on, no more.
// Whitespace runs collapse to one space on both sides, so stripping a
// space-surrounded mark (a Quranic waqf sign) never leaves a double space that
// would break an otherwise-contiguous phrase match. Pure.
import { foldSearch, foldSearchChar } from './arabic';

export interface HighlightSegment {
  text: string;
  match: boolean;
}

/** Return segments of ``text`` with every fold-insensitive occurrence of
    ``query`` flagged ``match: true``, whitespace-run-insensitively. Folding
    drops marks, 1:1-replaces letters, and collapses whitespace runs, so each
    kept folded character still maps back to a single original index. */
export function highlightSegments(text: string, query: string): HighlightSegment[] {
  const needle = foldSearch(query.trim()).replace(/\s+/g, ' ').trim();
  if (!needle || !text) return [{ text, match: false }];

  // Fold the text the same way, collapsing whitespace runs to one space so a
  // stripped space-surrounded mark cannot split the phrase. Each kept folded
  // character still maps to exactly one original index.
  let folded = '';
  const map: number[] = [];
  for (let i = 0; i < text.length; i += 1) {
    let f = foldSearchChar(text[i]);
    if (!f) continue;
    if (/\s/.test(f)) {
      if (folded.endsWith(' ')) continue;
      f = ' ';
    }
    folded += f;
    map.push(i);
  }

  const segments: HighlightSegment[] = [];
  let cursor = 0;
  let from = 0;
  for (;;) {
    const hit = folded.indexOf(needle, from);
    if (hit < 0) break;
    const startOrig = map[hit];
    const lastFolded = hit + needle.length - 1;
    const endOrig = lastFolded + 1 < map.length ? map[lastFolded + 1] : text.length;
    if (startOrig > cursor) segments.push({ text: text.slice(cursor, startOrig), match: false });
    segments.push({ text: text.slice(startOrig, endOrig), match: true });
    cursor = endOrig;
    from = lastFolded + 1;
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor), match: false });
  return segments;
}
