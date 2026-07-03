import { describe, expect, test } from 'vitest';

import { buildHash, parseHash, readerHref } from './routes';
import type { RouteState } from './routes';
import { toBase64Url } from './utils';

const reader: RouteState = {
  view: 'home',
  query: '',
  scope: '',
  cat: '',
  dom: '',
  reading: { urn: 'sY-50TSO', page: 12, query: '' },
  mode: 'exact',
  categories: [],
  book: '',
};

const home: RouteState = {
  view: 'home',
  query: '',
  scope: '',
  cat: '',
  dom: '',
  reading: null,
  mode: 'exact',
  categories: [],
  book: '',
};

describe('routes hash SSOT', () => {
  test('should round-trip a reader page', () => {
    expect(buildHash(reader)).toBe('#/read/sY-50TSO/12');
    expect(parseHash('#/read/sY-50TSO/12')).toEqual(reader);
  });

  test('should carry the reader highlight query, base64url-encoded', () => {
    const highlighted: RouteState = {
      ...reader,
      reading: { urn: 'sY-50TSO', page: 12, query: 'hadith' },
    };
    const hash = buildHash(highlighted);
    expect(hash).toBe(`#/read/sY-50TSO/12?q=${toBase64Url('hadith')}`);
    expect(hash).not.toContain('hadith');
    expect(parseHash(hash)).toEqual(highlighted);
  });

  test('should put home at the root and other views on their own path', () => {
    expect(buildHash(home)).toBe('#/');
    expect(buildHash({ ...home, view: 'library' })).toBe('#/library');
  });

  test('should layer an active search as a query string, the query base64url-encoded', () => {
    const searching: RouteState = {
      ...home,
      view: 'library',
      query: 'hadith',
      scope: 'content',
    };
    const hash = buildHash(searching);
    expect(hash).toBe(`#/library?q=${toBase64Url('hadith')}&scope=content`);
    expect(parseHash(hash)).toEqual(searching);
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
    expect(parseHash('#/read/sY-50TSO')).toEqual({
      ...reader,
      reading: { urn: 'sY-50TSO', page: 1, query: '' },
    });
  });

  test('should layer content-scope filters onto an active search, omitting the default mode', () => {
    const filtered: RouteState = {
      ...home,
      query: 'hadith',
      scope: 'content',
      categories: ['fiqh'],
    };
    const hash = buildHash(filtered);
    expect(hash).toBe(`#/?q=${toBase64Url('hadith')}&scope=content&category=fiqh`);
    expect(parseHash(hash)).toEqual(filtered);
  });

  test('should round-trip a non-default mode, multiple categories, and an Arabic book filter', () => {
    const filtered: RouteState = {
      ...home,
      query: 'hadith',
      scope: 'content',
      mode: 'broad',
      categories: ['hadith-general', 'fiqh'],
      book: 'بحار الأنوار',
    };
    const hash = buildHash(filtered);
    expect(hash).toBe(
      `#/?q=${toBase64Url('hadith')}&scope=content&mode=broad&category=hadith-general&category=fiqh&book=${toBase64Url('بحار الأنوار')}`,
    );
    expect(hash).not.toContain('بحار');
    expect(parseHash(hash)).toEqual(filtered);
  });

  test('should not serialize content filters for a non-content scope', () => {
    const worksSearch: RouteState = {
      ...home,
      query: 'hadith',
      scope: 'works',
      mode: 'broad',
      categories: ['fiqh'],
      book: 'x',
    };
    expect(buildHash(worksSearch)).toBe(`#/?q=${toBase64Url('hadith')}&scope=works`);
  });
});

describe('readerHref', () => {
  test('should match the hash buildHash produces for the same reading position', () => {
    expect(readerHref('sY-50TSO', 12)).toBe(buildHash(reader));
    expect(readerHref('sY-50TSO', 12)).toBe('#/read/sY-50TSO/12');
  });

  test('should carry an optional highlight query, base64url-encoded and trimmed', () => {
    expect(readerHref('sY-50TSO', 12, 'hadith')).toBe(`#/read/sY-50TSO/12?q=${toBase64Url('hadith')}`);
    expect(readerHref('sY-50TSO', 12, '  ')).toBe('#/read/sY-50TSO/12');
  });
});
