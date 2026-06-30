import { describe, expect, test } from 'vitest';

import { buildHash, parseHash } from './routes';
import type { RouteState } from './routes';

const reader: RouteState = {
  view: 'home',
  query: '',
  scope: '',
  reading: { urn: 'sY-50TSO', page: 12 },
};

const home: RouteState = { view: 'home', query: '', scope: '', reading: null };

describe('routes hash SSOT', () => {
  test('should round-trip a reader page', () => {
    expect(buildHash(reader)).toBe('#/read/sY-50TSO/12');
    expect(parseHash('#/read/sY-50TSO/12')).toEqual(reader);
  });

  test('should put home at the root and other views on their own path', () => {
    expect(buildHash(home)).toBe('#/');
    expect(buildHash({ view: 'library', query: '', scope: '', reading: null })).toBe('#/library');
  });

  test('should layer an active search as a query string', () => {
    const searching: RouteState = {
      view: 'library',
      query: 'hadith',
      scope: 'content',
      reading: null,
    };
    expect(buildHash(searching)).toBe('#/library?q=hadith&scope=content');
    expect(parseHash('#/library?q=hadith&scope=content')).toEqual(searching);
  });

  test('should fall back to the default view for unknown or empty hashes', () => {
    expect(parseHash('#/nonsense')).toEqual(home);
    expect(parseHash('')).toEqual(home);
    expect(parseHash('#')).toEqual(home);
  });

  test('should default a missing reader page to the first page', () => {
    expect(parseHash('#/read/sY-50TSO')).toEqual({
      view: 'home',
      query: '',
      scope: '',
      reading: { urn: 'sY-50TSO', page: 1 },
    });
  });
});
