// reading.ts — the one place the reader's last position is stored and read.
// No accounts: continuity lives in localStorage. The stored shape is validated
// on read; an entry that no longer parses or points at a book the catalogue
// no longer serves is stale local state, so callers remove it (cache hygiene,
// not a data fallback — the corpus itself is never guessed at).

import { READING } from './constants';

export interface ReadingPosition {
  urn: string;
  page: number;
  at: number;
}

function isPosition(value: unknown): value is ReadingPosition {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.urn === 'string' && typeof v.page === 'number' && typeof v.at === 'number';
}

/** Persist the current reading position (called as the reader turns pages). */
export function saveReading(urn: string, page: number): void {
  const position: ReadingPosition = { urn, page, at: Date.now() };
  localStorage.setItem(READING.STORAGE_KEY, JSON.stringify(position));
}

/** The last stored position, or null. A malformed entry is removed on sight. */
export function lastReading(): ReadingPosition | null {
  const raw = localStorage.getItem(READING.STORAGE_KEY);
  if (raw === null) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw) as unknown;
  } catch {
    localStorage.removeItem(READING.STORAGE_KEY);
    return null;
  }
  if (!isPosition(parsed)) {
    localStorage.removeItem(READING.STORAGE_KEY);
    return null;
  }
  return parsed;
}

/** Drop the stored position (stale URN, or the user finished the book). */
export function clearReading(): void {
  localStorage.removeItem(READING.STORAGE_KEY);
}
