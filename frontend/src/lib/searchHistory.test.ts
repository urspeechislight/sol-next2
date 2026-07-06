import { describe, expect, test, vi } from 'vitest';

import { withRecordedSearch } from './searchHistory';
import type { SearchHistoryEntry } from './searchHistory';

const entry = (
  query: string,
  scope: SearchHistoryEntry['scope'],
  at: number,
): SearchHistoryEntry => ({ query, scope, at });

describe('withRecordedSearch', () => {
  test('should prepend a new entry as most recent', () => {
    vi.spyOn(Date, 'now').mockReturnValue(100);
    const next = withRecordedSearch([entry('older', 'content', 1)], 'newest', 'content');
    expect(next).toEqual([entry('newest', 'content', 100), entry('older', 'content', 1)]);
  });

  test('should dedupe an existing query in the same scope, moving it to the front', () => {
    vi.spyOn(Date, 'now').mockReturnValue(200);
    const existing = [entry('kept', 'content', 1), entry('hadith', 'narrator', 2)];
    const next = withRecordedSearch(existing, 'hadith', 'narrator');
    expect(next).toEqual([entry('hadith', 'narrator', 200), entry('kept', 'content', 1)]);
  });

  test('should dedupe case-insensitively', () => {
    vi.spyOn(Date, 'now').mockReturnValue(300);
    const next = withRecordedSearch([entry('Bukhari', 'works', 1)], 'bukhari', 'works');
    expect(next).toEqual([entry('bukhari', 'works', 300)]);
  });

  test('should keep the same query text in two different scopes as distinct entries', () => {
    vi.spyOn(Date, 'now').mockReturnValue(400);
    const next = withRecordedSearch([entry('light', 'quran', 1)], 'light', 'content');
    expect(next).toEqual([entry('light', 'content', 400), entry('light', 'quran', 1)]);
  });

  test('should trim the recorded query', () => {
    vi.spyOn(Date, 'now').mockReturnValue(500);
    const next = withRecordedSearch([], '  spaced  ', 'content');
    expect(next).toEqual([entry('spaced', 'content', 500)]);
  });

  test('should ignore a blank query and return the list unchanged', () => {
    const existing = [entry('kept', 'content', 1)];
    expect(withRecordedSearch(existing, '   ', 'content')).toEqual(existing);
  });

  test('should cap the list at MAX_ENTRIES, dropping the oldest tail entry', () => {
    const existing = Array.from({ length: 8 }, (_, i) => entry(`q${i}`, 'content', i));
    vi.spyOn(Date, 'now').mockReturnValue(900);
    const next = withRecordedSearch(existing, 'newest', 'content');
    expect(next).toHaveLength(8);
    expect(next[0]).toEqual(entry('newest', 'content', 900));
    expect(next[next.length - 1]).toEqual(entry('q6', 'content', 6));
    expect(next.some((e) => e.query === 'q7')).toBe(false);
  });
});
