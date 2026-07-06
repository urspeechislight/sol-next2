import { describe, expect, it } from 'vitest';

import {
  groupState,
  scopeTokens,
  toggleGroup,
  toggleOne,
  wireCategories,
} from './taxonomySelection';

const FIQH = { id: 'fiqh', label: 'Fiqh', slugs: ['hanafi', 'maliki', 'zahiri'] };
const HADITH = { id: 'hadith', label: 'Hadith', slugs: ['sunni-hadith'] };

describe('groupState', () => {
  it('should derive none, partial, and all from the flat set', () => {
    expect(groupState(FIQH.slugs, new Set())).toBe('none');
    expect(groupState(FIQH.slugs, new Set(['maliki']))).toBe('partial');
    expect(groupState(FIQH.slugs, new Set(FIQH.slugs))).toBe('all');
  });
});

describe('toggleOne', () => {
  it('should add and remove a slug without mutating the input', () => {
    const base = new Set(['hanafi']);
    const added = toggleOne(base, 'maliki');
    expect([...added].sort()).toEqual(['hanafi', 'maliki']);
    expect(toggleOne(added, 'hanafi').has('hanafi')).toBe(false);
    expect(base.size).toBe(1);
  });
});

describe('toggleGroup', () => {
  it('should select the whole group when any member is missing', () => {
    const next = toggleGroup(new Set(['hanafi']), FIQH.slugs);
    expect(groupState(FIQH.slugs, next)).toBe('all');
  });

  it('should release the whole group when fully selected, keeping others', () => {
    const full = new Set([...FIQH.slugs, 'sunni-hadith']);
    const next = toggleGroup(full, FIQH.slugs);
    expect(groupState(FIQH.slugs, next)).toBe('none');
    expect(next.has('sunni-hadith')).toBe(true);
  });
});

describe('scopeTokens', () => {
  const labelOf = (s: string) => s.toUpperCase();

  it('should collapse a fully selected group into one group token', () => {
    const tokens = scopeTokens([FIQH, HADITH], new Set([...FIQH.slugs, 'sunni-hadith']), labelOf);
    expect(tokens).toEqual([
      { kind: 'group', id: 'fiqh', label: 'Fiqh' },
      { kind: 'group', id: 'hadith', label: 'Hadith' },
    ]);
  });

  it('should list partial selections as loose category tokens', () => {
    const tokens = scopeTokens([FIQH, HADITH], new Set(['maliki', 'sunni-hadith']), labelOf);
    expect(tokens).toEqual([
      { kind: 'group', id: 'hadith', label: 'Hadith' },
      { kind: 'category', id: 'maliki', label: 'MALIKI' },
    ]);
  });

  it('should keep selections no group covers instead of dropping them', () => {
    const tokens = scopeTokens([FIQH], new Set(['lost-slug']), labelOf);
    expect(tokens).toEqual([{ kind: 'category', id: 'lost-slug', label: 'LOST-SLUG' }]);
  });
});

describe('wireCategories', () => {
  it('should serialize the selection as a stable sorted list', () => {
    expect(wireCategories(new Set(['b', 'a']))).toEqual(['a', 'b']);
  });
});
