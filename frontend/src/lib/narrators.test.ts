import { describe, expect, test } from 'vitest';

import { annotateText, buildNarratorIndex, narratorToRecord } from './narrators';
import type { NarratorDetail } from './types';

// A served NarratorDetail: every field present (Full<> restores the defaults
// pydantic marks optional), tiers exercising the top-grade pick.
const detail: NarratorDetail = {
  id: 512,
  primary_name_ar: 'محمد بن عثمان بن أبي شيبة',
  primary_name_en: 'Muhammad ibn Uthman ibn Abi Shayba',
  kunya: 'أبو جعفر',
  nisba: 'العبسي',
  tradition: 'hanafi',
  birth_year_ah: 150,
  death_year_ah: 237,
  death_year_ce: '851 CE',
  tabaqa: 'من العاشرة',
  living_city: 'بغداد',
  death_place: 'بغداد',
  category: 'clean',
  alias_count: 4,
  teacher_count: 12,
  student_count: 130,
  aliases: [
    { name_ar: 'محمد بن عثمان', name_role: 'variant', source_label: 'Tahdhīb al-Kamāl' },
    { name_ar: 'أبو جعفر', name_role: 'kunya', source_label: 'Tahdhīb al-Kamāl' },
  ],
  grades: [
    {
      term: 'صدوق',
      tier: 'saduq',
      evaluator: 'Ibn Hajar Al-Asqalani',
      source_label: 'Taqrib al-Tahdhib',
      source_book: 'ibnhajar-taqrib',
      source_locator: '50',
    },
    {
      term: 'ثقه',
      tier: 'thiqa',
      evaluator: 'Ibn Abi Hatim Al-Razi',
      source_label: 'Al-Jarh wa-l-Taʿdil',
      source_book: 'ibnabihatim-jarh',
      source_locator: '269',
    },
  ],
  stances: [{ predicate: 'position-toward-ahl-al-bayt', value_text: 'sincere_believer' }],
  tarjama: ['حدث عن ابن عيينة…'],
};

describe('narratorToRecord', () => {
  test('should map the served detail onto the reader record shape', () => {
    const record = narratorToRecord(detail);
    expect(record).toEqual({
      id: 512,
      narrator_id: 512,
      primary_name_ar: 'محمد بن عثمان بن أبي شيبة',
      primary_name_en: 'Muhammad ibn Uthman ibn Abi Shayba',
      kunya: 'أبو جعفر',
      nisba: 'العبسي',
      tradition: 'hanafi',
      birth_year_ah: 150,
      death_year_ah: 237,
      death_year_ce: '851 CE',
      teacher_count: 12,
      student_count: 130,
      tier: 'thiqa',
    });
  });

  test('should pick the highest-ranked tier among the recorded grades', () => {
    expect(narratorToRecord(detail).tier).toBe('thiqa');
    const weak: NarratorDetail = {
      ...detail,
      grades: [detail.grades[0]!, { ...detail.grades[1]!, tier: 'daif', term: 'ضعيف' }],
    };
    expect(narratorToRecord(weak).tier).toBe('saduq');
  });

  test('should have no tier when no grade is recorded', () => {
    expect(narratorToRecord({ ...detail, grades: [] }).tier).toBeNull();
  });
});

describe('buildNarratorIndex over the merged record shape', () => {
  test('should index by the primary Arabic name tokens', () => {
    const index = buildNarratorIndex([narratorToRecord(detail)]);
    expect(index.size).toBe(1);
    const segs = annotateText('حدثنا محمد بن عثمان بن أبي شيبة قال', index);
    const hit = segs.find((s) => s.type === 'narrator');
    expect(hit).toMatchObject({ type: 'narrator', record: { id: 512 } });
  });

  test('should skip single-token names as too ambiguous to link', () => {
    const index = buildNarratorIndex([
      { ...narratorToRecord(detail), primary_name_ar: 'مالك', id: 9 },
    ]);
    expect(index.size).toBe(0);
  });
});
