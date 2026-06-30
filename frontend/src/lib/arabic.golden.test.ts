import { describe, it, expect } from 'vitest';
import { foldSearch, normalizeName } from './arabic';
// The one cross-stack table; the backend asserts the same file in
// tests/test_fold_golden.py, so the two folds can never drift apart.
import golden from '../../../tests/fixtures/arabic_fold_golden.json';

describe('arabic folds vs the cross-stack golden table', () => {
  it('should match the backend fold_search table when folding for search', () => {
    for (const c of golden.fold_search) expect(foldSearch(c.in)).toBe(c.out);
  });

  it('should match the backend normalize_arabic table when normalizing names', () => {
    for (const c of golden.normalize_name) expect(normalizeName(c.in)).toBe(c.out);
  });
});
