import { describe, expect, test } from 'vitest';

import { SURAHS, surahName } from './surahs';

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
