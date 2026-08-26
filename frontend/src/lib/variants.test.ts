import { describe, expect, test } from 'vitest';

import { topTier } from './variants';

describe('topTier', () => {
  test('should return the highest-ranked tier among the recorded grades', () => {
    expect(topTier(['daif', 'thiqa', 'saduq'])).toBe('thiqa');
    expect(topTier(['matruk', 'majhul'])).toBe('majhul');
  });

  test('should rank thiqa above saduq above maqbul', () => {
    expect(topTier(['maqbul', 'saduq'])).toBe('saduq');
    expect(topTier(['maqbul'])).toBe('maqbul');
  });

  test('should pass over unknown tiers and return empty for none', () => {
    expect(topTier(['unrecorded', 'matruk'])).toBe('matruk');
    expect(topTier(['unrecorded'])).toBe('');
    expect(topTier([])).toBe('');
  });
});
