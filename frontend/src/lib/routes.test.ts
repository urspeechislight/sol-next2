import { describe, expect, test } from 'vitest';

import { buildHash, parseHash } from './routes';
import type { RouteState } from './routes';

const reader: RouteState = {
  view: 'home',
  query: '',
  scope: '',
  cat: '',
  dom: '',
  reading: { urn: 'sY-50TSO', page: 12 },
};

const home: RouteState = { view: 'home', query: '', scope: '', cat: '', dom: '', reading: null };

describe('routes hash SSOT', () => {
  test('should round-trip a reader page', () => {
    expect(buildHash(reader)).toBe('#/read/sY-50TSO/12');
    expect(parseHash('#/read/sY-50TSO/12')).toEqual(reader);
  });

  test('should put home at the root and other views on their own path', () => {
    expect(buildHash(home)).toBe('#/');
    expect(buildHash({ ...home, view: 'library' })).toBe('#/library');
  });

  test('should layer an active search as a query string', () => {
    const searching: RouteState = {
      ...home,
      view: 'library',
      query: 'hadith',
      scope: 'content',
    };
    expect(buildHash(searching)).toBe('#/library?q=hadith&scope=content');
    expect(parseHash('#/library?q=hadith&scope=content')).toEqual(searching);
  });

  test('should round-trip a library category deep-link', () => {
    const scoped: RouteState = { ...home, view: 'library', cat: 'shia-hadith-general' };
    expect(buildHash(scoped)).toBe('#/library?cat=shia-hadith-general');
    expect(parseHash('#/library?cat=shia-hadith-general')).toEqual(scoped);
  });

  test('should round-trip a library domain deep-link, category winning over domain', () => {
    const scoped: RouteState = { ...home, view: 'library', dom: 'hadith' };
    expect(buildHash(scoped)).toBe('#/library?dom=hadith');
    expect(parseHash('#/library?dom=hadith')).toEqual(scoped);
    expect(buildHash({ ...scoped, cat: 'shia-hadith-general' })).toBe(
      '#/library?cat=shia-hadith-general',
    );
  });

  test('should ignore library scope params on other views', () => {
    expect(parseHash('#/graph?cat=shia-hadith-general')).toEqual({ ...home, view: 'graph' });
  });

  test('should fall back to the default view for unknown or empty hashes', () => {
    expect(parseHash('#/nonsense')).toEqual(home);
    expect(parseHash('')).toEqual(home);
    expect(parseHash('#')).toEqual(home);
  });

  test('should default a missing reader page to the first page', () => {
    expect(parseHash('#/read/sY-50TSO')).toEqual({ ...reader, reading: { urn: 'sY-50TSO', page: 1 } });
  });
});
