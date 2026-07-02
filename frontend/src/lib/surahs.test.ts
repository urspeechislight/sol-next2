import { describe, expect, test } from 'vitest';

import type { Ayah } from './types';
import { SURAHS, matchSurahs, parseVerseRef, surahName, verseMatches } from './surahs';

describe('SURAHS', () => {
  test('should carry all 114 surahs in order', () => {
    expect(SURAHS).toHaveLength(114);
    SURAHS.forEach((s, i) => {
      expect(s.n).toBe(i + 1);
      expect(s.ar.length).toBeGreaterThan(0);
      expect(s.en.length).toBeGreaterThan(0);
    });
  });
});

describe('surahName', () => {
  test('should resolve a number to its names', () => {
    expect(surahName(67).en).toBe('al-Mulk');
    expect(surahName(1).ar).toBe('الفاتحة');
  });

  test('should fail loud on an out-of-range number', () => {
    expect(() => surahName(0)).toThrow('Unknown surah number');
    expect(() => surahName(115)).toThrow('Unknown surah number');
  });
});

describe('parseVerseRef', () => {
  test('should parse a surah:ayah reference and reject anything else', () => {
    expect(parseVerseRef('55:5')).toEqual({ surah: 55, ayah: 5 });
    expect(parseVerseRef(' 2 : 255 ')).toEqual({ surah: 2, ayah: 255 });
    expect(parseVerseRef('rahman')).toBeNull();
    expect(parseVerseRef('55')).toBeNull();
  });
});

describe('matchSurahs', () => {
  test('should match by English name, Arabic name, and number', () => {
    expect(matchSurahs('mulk').map((s) => s.n)).toContain(67);
    expect(matchSurahs('الفاتحه').map((s) => s.n)).toContain(1);
    expect(matchSurahs('114').map((s) => s.n)).toEqual([114]);
  });

  test('should return every surah for an empty query', () => {
    expect(matchSurahs('  ')).toHaveLength(114);
  });
});

describe('verseMatches', () => {
  const verse: Ayah = {
    surah: 68,
    ayah: 4,
    text_ar: 'وَإِنَّكَ لَعَلَىٰ خُلُقٍ عَظِيمٍ',
    text_en: 'You stand on an exalted standard of character.',
    text_plain: 'وإنك لعلى خلق عظيم',
    verse_count: 52,
  };

  test('should match Arabic vowel-insensitively', () => {
    expect(verseMatches(verse, 'خلق عظيم')).toBe(true);
    expect(verseMatches(verse, 'خُلُقٍ')).toBe(true);
    expect(verseMatches(verse, 'الرحمن')).toBe(false);
  });

  test('should match the English rendering case-insensitively', () => {
    expect(verseMatches(verse, 'EXALTED standard')).toBe(true);
    expect(verseMatches(verse, 'mercy')).toBe(false);
  });
});
