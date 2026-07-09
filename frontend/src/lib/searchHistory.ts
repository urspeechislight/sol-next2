// searchHistory.ts — the one place the header's past searches are stored and
// read. No accounts: continuity lives in localStorage, the same model as
// reading.ts. withRecordedSearch is the pure list fold (tested below);
// everything past it is a thin localStorage wrapper plus a reactive
// useSyncExternalStore, mirroring useTheme.ts, so the header's dropdown
// updates the moment any tab records, removes, or clears an entry.

import { useSyncExternalStore } from 'react';

import type { SearchScope } from './api/client';
import { SEARCH_HISTORY } from './constants';
import { createSubscribable } from './subscribable';

export interface SearchHistoryEntry {
  query: string;
  scope: SearchScope;
  at: number;
}

function isEntry(value: unknown): value is SearchHistoryEntry {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.query === 'string' && typeof v.scope === 'string' && typeof v.at === 'number';
}

function isEntryList(value: unknown): value is SearchHistoryEntry[] {
  return Array.isArray(value) && value.every(isEntry);
}

/** Fold one committed search into the list: most-recent-first, deduped by
    query+scope (case-insensitive on the query), capped at MAX_ENTRIES. Pure,
    so the fold logic is tested without a localStorage/DOM environment. */
export function withRecordedSearch(
  entries: readonly SearchHistoryEntry[],
  query: string,
  scope: SearchScope,
): SearchHistoryEntry[] {
  const trimmed = query.trim();
  if (!trimmed) return [...entries];
  const rest = entries.filter(
    (e) => !(e.scope === scope && e.query.toLowerCase() === trimmed.toLowerCase()),
  );
  return [{ query: trimmed, scope, at: Date.now() }, ...rest].slice(0, SEARCH_HISTORY.MAX_ENTRIES);
}

const { subscribe, notify } = createSubscribable();
let cache: { raw: string | null; entries: SearchHistoryEntry[] } = { raw: null, entries: [] };

/** getSnapshot for useSyncExternalStore: must return the SAME reference when
    the stored value hasn't changed, so it caches against the raw string
    instead of re-parsing (and re-allocating) on every render. */
function read(): SearchHistoryEntry[] {
  const raw = localStorage.getItem(SEARCH_HISTORY.STORAGE_KEY);
  if (raw === cache.raw) return cache.entries;
  let parsed: unknown;
  try {
    parsed = raw === null ? [] : (JSON.parse(raw) as unknown);
  } catch {
    localStorage.removeItem(SEARCH_HISTORY.STORAGE_KEY);
    cache = { raw: null, entries: [] };
    return cache.entries;
  }
  if (!isEntryList(parsed)) {
    localStorage.removeItem(SEARCH_HISTORY.STORAGE_KEY);
    cache = { raw: null, entries: [] };
    return cache.entries;
  }
  cache = { raw, entries: parsed };
  return cache.entries;
}

function write(entries: SearchHistoryEntry[]): void {
  const raw = JSON.stringify(entries);
  localStorage.setItem(SEARCH_HISTORY.STORAGE_KEY, raw);
  cache = { raw, entries };
  notify();
}

/** Record a completed search: called once a search actually runs (Enter, or
    a result that launches a new query) — never on every keystroke. */
export function recordSearch(query: string, scope: SearchScope): void {
  if (!query.trim()) return;
  write(withRecordedSearch(read(), query, scope));
}

/** Drop one entry, e.g. its row's remove button. */
export function removeSearch(query: string, scope: SearchScope): void {
  write(read().filter((e) => !(e.query === query && e.scope === scope)));
}

/** Drop the whole list, e.g. the dropdown's "Clear recent searches". */
export function clearSearchHistory(): void {
  write([]);
}

/** The reactive search history: re-renders every consumer the moment any of
    them records, removes, or clears an entry. */
export function useSearchHistory(): SearchHistoryEntry[] {
  return useSyncExternalStore(subscribe, read);
}
