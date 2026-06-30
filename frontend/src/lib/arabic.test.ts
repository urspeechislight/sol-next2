import { describe, expect, test } from 'vitest';

import { foldNameChar, foldSearch, normalizeName } from './arabic';

describe('foldSearch (text-search fold, mirrors backend fold_search)', () => {
  test('should fold alef-hamza to bare alef so spellings match', () => {
    expect(foldSearch('أَوْلِيَاءَ')).toBe(foldSearch('اولياء'));
    expect(foldSearch('إنسان')).toBe(foldSearch('انسان'));
  });

  test('should fold alef-maqsura to yaa and taa-marbuta to haa', () => {
    expect(foldSearch('عَلَى')).toBe(foldSearch('علي'));
    expect(foldSearch('مكتبة')).toBe(foldSearch('مكتبه'));
  });

  test('should strip Quranic annotation signs rather than tokenise them', () => {
    const folded = foldSearch('جَهَنَّمُ ۖ وَلَا');
    expect(folded.includes('ۖ')).toBe(false);
    expect(folded.split(/\s+/).filter(Boolean)).toEqual(['جهنم', 'ولا']);
  });
});

describe('normalizeName (name fold, mirrors backend normalize_arabic)', () => {
  test('should fold letters, drop non-Arabic, and collapse whitespace', () => {
    expect(normalizeName('عَلِيّ   بنُ  أبي')).toBe('علي بن ابي');
  });

  test('should drop a harakat but keep a bare letter', () => {
    expect(foldNameChar('ل')).toBe('ل');
    expect(foldNameChar('َ')).toBe('');
  });
});
