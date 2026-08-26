import { describe, expect, test } from 'vitest';

import {
  categoryLabel,
  gradeLabel,
  stancePredicateLabel,
  stanceValueLabel,
  traditionLabel,
} from './labels';

describe('gradeLabel', () => {
  test('should label the Arabic verdict terms and the tier keys identically', () => {
    expect(gradeLabel('ثقه')).toBe(gradeLabel('thiqa'));
    expect(gradeLabel('مجهول')).toBe(gradeLabel('majhul'));
    expect(gradeLabel('صدوق')).toBe(gradeLabel('saduq'));
    expect(gradeLabel('صحابي')).toBe(gradeLabel('sahabi'));
  });

  test('should pass unknown terms through unchanged', () => {
    expect(gradeLabel('لا بأس به')).toBe('لا بأس به');
  });
});

describe('traditionLabel', () => {
  test('should label the registry traditions', () => {
    expect(traditionLabel('imami')).toBe('Imāmī');
    expect(traditionLabel('shafii')).toBe('Shāfiʿī');
    expect(traditionLabel('unknown-school')).toBe('unknown-school');
  });
});

describe('categoryLabel', () => {
  test('should label the entry classes', () => {
    expect(categoryLabel('clean')).toBe('Clean');
    expect(categoryLabel('long_entry')).toBe('Long entry');
    expect(categoryLabel('isnad_fragment')).toBe('Isnād fragment');
    expect(categoryLabel('odd')).toBe('odd');
  });
});

describe('stance labels', () => {
  test('should label the ALID stance vocabulary', () => {
    expect(stancePredicateLabel('position-toward-ahl-al-bayt')).toBe(
      'Position toward the Ahl al-Bayt',
    );
    expect(stanceValueLabel('sincere_believer')).toBe('Sincere believer');
    expect(stanceValueLabel('hypocrite_or_hostile')).toBe('Hostile or a hypocrite');
    expect(stancePredicateLabel('other-predicate')).toBe('other-predicate');
  });
});
