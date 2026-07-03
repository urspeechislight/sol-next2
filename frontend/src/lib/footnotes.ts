// footnotes.ts: the reader's footnote-marker tokenizer. Splits page text into
// text / marker segments so the printed marker characters («1», spaced « 1 »,
// or mid-line (1)) can be wrapped and styled WITHOUT being rewritten: copied
// text stays byte-identical to the corpus. A candidate counts as a marker only
// when its number has a numbered apparatus entry on the page (the entry-set
// gate) and, for the paren form, when it does not open a line: a line-start
// (N) is a digitized footnote-entry head that leaked into body text (~1% of
// corpus pages), not a reference. Both rules were measured corpus-wide before
// freezing (2026-07-03 dry run over 3.2M numbered footnote pages). Pure.

export type FootnoteSegment =
  | { type: 'text'; value: string }
  | { type: 'marker'; value: string; marker: string };

const CANDIDATE = /«\s*(\d+)\s*»|\((\d+)\)/g;

function opensLine(text: string, index: number): boolean {
  const lineStart = text.lastIndexOf('\n', index - 1) + 1;
  return /^[ \t]*$/.test(text.slice(lineStart, index));
}

/** Split ``text`` into text / marker segments against the page's numbered
    entry set. Marker segments keep the printed characters in ``value`` and
    carry the bare number in ``marker``; concatenating every segment's
    ``value`` reproduces ``text`` exactly. */
export function footnoteSegments(
  text: string,
  entryMarkers: ReadonlySet<string>,
): FootnoteSegment[] {
  if (!text) return [];
  if (entryMarkers.size === 0) return [{ type: 'text', value: text }];
  const segments: FootnoteSegment[] = [];
  let cursor = 0;
  CANDIDATE.lastIndex = 0;
  for (let m = CANDIDATE.exec(text); m !== null; m = CANDIDATE.exec(text)) {
    const marker = m[1] ?? m[2];
    if (marker === undefined) {
      throw new Error(`footnote candidate matched without digits: ${m[0]}`);
    }
    const isParen = m[2] !== undefined;
    if (!entryMarkers.has(marker)) continue;
    if (isParen && opensLine(text, m.index)) continue;
    if (m.index > cursor) segments.push({ type: 'text', value: text.slice(cursor, m.index) });
    segments.push({ type: 'marker', value: m[0], marker });
    cursor = m.index + m[0].length;
  }
  if (cursor < text.length) segments.push({ type: 'text', value: text.slice(cursor) });
  return segments;
}

/** The entry numbers whose markers actually occur in ``text``: an apparatus
    entry links back to the body only when its number is in this set. */
export function matchedMarkers(
  text: string,
  entryMarkers: ReadonlySet<string>,
): ReadonlySet<string> {
  const found = new Set<string>();
  for (const seg of footnoteSegments(text, entryMarkers)) {
    if (seg.type === 'marker') found.add(seg.marker);
  }
  return found;
}
