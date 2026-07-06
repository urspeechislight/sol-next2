// Tests for the footnote-marker tokenizer: entry-set gate, line-start
// exclusion, printed-glyph preservation (round-trip identity), and the
// matched-markers projection that drives apparatus backlinks.
import { describe, expect, it } from 'vitest';

import { footnoteSegments, matchedMarkers } from './footnotes';

const ENTRIES = new Set(['1', '2']);

describe('footnoteSegments', () => {
  it('should tokenize a guillemet marker and preserve its printed glyphs', () => {
    const segs = footnoteSegments('النص «1» بعده', ENTRIES);
    expect(segs).toEqual([
      { type: 'text', value: 'النص ' },
      { type: 'marker', value: '«1»', marker: '1' },
      { type: 'text', value: ' بعده' },
    ]);
  });

  it('should preserve spacing inside a spaced guillemet marker', () => {
    const segs = footnoteSegments('النص « 1 » بعده', ENTRIES);
    expect(segs[1]).toEqual({ type: 'marker', value: '« 1 »', marker: '1' });
  });

  it('should tokenize a mid-line paren marker', () => {
    const segs = footnoteSegments('قال اختلفته (1) أي جعلته خلفي', ENTRIES);
    expect(segs.map((s) => s.type)).toEqual(['text', 'marker', 'text']);
    expect(segs[1]).toEqual({ type: 'marker', value: '(1)', marker: '1' });
  });

  it('should tokenize a spaced mid-line paren marker and preserve its spacing', () => {
    const segs = footnoteSegments('وبأسرار علمهم أينعت ( 1 ) ثمار العرفان', ENTRIES);
    expect(segs[1]).toEqual({ type: 'marker', value: '( 1 )', marker: '1' });
  });

  it('should not let a paren candidate span a line break', () => {
    const segs = footnoteSegments('نص (\n1) بعده', ENTRIES);
    expect(segs).toEqual([{ type: 'text', value: 'نص (\n1) بعده' }]);
  });

  it('should exclude a line-start paren candidate as a leaked entry head', () => {
    const segs = footnoteSegments('سطر أول\n(1) نص حاشية مسرب\nسطر ثان «2» نهاية', ENTRIES);
    const markers = segs.filter((s) => s.type === 'marker');
    expect(markers).toEqual([{ type: 'marker', value: '«2»', marker: '2' }]);
  });

  it('should leave candidates outside the entry set as plain text', () => {
    const segs = footnoteSegments('ولد سنة (1984) وقيل «7» غيرها', ENTRIES);
    expect(segs).toEqual([{ type: 'text', value: 'ولد سنة (1984) وقيل «7» غيرها' }]);
  });

  it('should return one text segment when the page has no numbered entries', () => {
    expect(footnoteSegments('نص فيه «1»', new Set())).toEqual([
      { type: 'text', value: 'نص فيه «1»' },
    ]);
  });

  it('should return no segments for empty text', () => {
    expect(footnoteSegments('', ENTRIES)).toEqual([]);
  });

  it('should round-trip the input exactly when segment values are concatenated', () => {
    const text = 'أ «1» ب (2) ج\n(1) سطر مسرب\nد « 2 » ه ( 1 ) و (1984)';
    const joined = footnoteSegments(text, ENTRIES)
      .map((s) => s.value)
      .join('');
    expect(joined).toBe(text);
  });
});

describe('matchedMarkers', () => {
  it('should collect each matched number once across repeated occurrences', () => {
    const found = matchedMarkers('«1» ثم (1) ثم « 2 » و ( 2 )', ENTRIES);
    expect([...found].sort()).toEqual(['1', '2']);
  });

  it('should be empty when nothing matches', () => {
    expect(matchedMarkers('نص بلا إحالات', ENTRIES).size).toBe(0);
  });
});
